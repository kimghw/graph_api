"""Graph API 게이트웨이 모듈

이 모듈은 Microsoft Graph API와의 통신을 처리합니다.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import GraphApiError, DeltaLinkError
from src.infra.config import Config
from src.infra.auth_token import AuthTokenManager
from src.schemas.email import EmailDto, EmailFilter, EmailProcessingOptions


# 로거 설정
logger = LoggerFactory.get_logger(__name__)


class GraphApiGateway:
    """Graph API 게이트웨이 클래스
    
    Microsoft Graph API와의 통신을 처리합니다.
    """
    
    def __init__(self, auth_manager: Optional[AuthTokenManager] = None):
        """초기화 메소드
        
        Args:
            auth_manager (Optional[AuthTokenManager], optional): 인증 토큰 관리자.
                지정하지 않으면 기본 인스턴스 생성.
        """
        self.auth_manager = auth_manager or AuthTokenManager()
        self.api_url = Config.get_api_url()
        logger.debug(f"GraphApiGateway 초기화 완료 (API URL: {self.api_url})")
    
    def get_me(self) -> Dict[str, Any]:
        """현재 사용자 정보를 조회합니다.
        
        Returns:
            Dict[str, Any]: 사용자 정보
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        return self._make_request("GET", "/me")
    
    def get_messages(
        self, 
        filter_options: EmailFilter,
        processing_options: Optional[EmailProcessingOptions] = None
    ) -> List[EmailDto]:
        """메시지를 조회합니다.
        
        Args:
            filter_options (EmailFilter): 필터 옵션
            processing_options (Optional[EmailProcessingOptions], optional): 처리 옵션
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        if processing_options is None:
            processing_options = EmailProcessingOptions()
            
        folder = filter_options.folder or "inbox"
        url = self._build_message_url(folder)
        
        # 쿼리 파라미터 생성
        params = {
            "$top": filter_options.limit,
            "$select": "id,subject,bodyPreview,body,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,isRead,importance,hasAttachments,conversationId,categories"
        }
        
        # OData 필터 추가
        filter_query = filter_options.get_filter_query()
        if filter_query:
            params["$filter"] = filter_query
            
        # 정렬 추가
        if folder == "sentItems":
            params["$orderby"] = "sentDateTime desc"
        else:
            params["$orderby"] = "receivedDateTime desc"
        
        # API 요청
        response = self._make_request("GET", url, params=params)
        
        # 응답 처리
        messages = response.get("value", [])
        logger.debug(f"{len(messages)}개의 메시지 조회됨")
        
        # EmailDto 변환
        email_dtos = []
        
        for message in messages:
            # 필터 적용
            if processing_options.apply_filters:
                sender = message.get("from", {}).get("emailAddress", {})
                sender_email = sender.get("address", "")
                sender_name = sender.get("name", "")
                
                if filter_options.should_exclude_sender(sender_email, sender_name):
                    logger.debug(f"필터링된 발신자: {sender_name} <{sender_email}>")
                    continue
            
            # DTO 변환
            email_dto = EmailDto.from_dict(message, processing_options)
            email_dtos.append(email_dto)
        
        return email_dtos
    
    def get_message(
        self,
        message_id: str,
        processing_options: Optional[EmailProcessingOptions] = None
    ) -> EmailDto:
        """특정 메시지를 조회합니다.
        
        Args:
            message_id (str): 메시지 ID
            processing_options (Optional[EmailProcessingOptions], optional): 처리 옵션
            
        Returns:
            EmailDto: 이메일 DTO
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        if processing_options is None:
            processing_options = EmailProcessingOptions()
            
        url = f"/me/messages/{message_id}"
        
        # 첨부 파일 포함 여부
        expand = None
        if processing_options.include_attachments:
            expand = "attachments"
            
        # API 요청
        response = self._make_request("GET", url, expand=expand)
        
        # EmailDto 변환
        return EmailDto.from_dict(response, processing_options)
    
    def get_delta_messages(
        self,
        folder: str = "inbox",
        processing_options: Optional[EmailProcessingOptions] = None
    ) -> Tuple[List[EmailDto], Optional[str]]:
        """델타 쿼리로 변경된 메시지를 조회합니다.
        
        Args:
            folder (str, optional): 폴더. 기본값은 "inbox".
            processing_options (Optional[EmailProcessingOptions], optional): 처리 옵션
            
        Returns:
            Tuple[List[EmailDto], Optional[str]]: 
                이메일 DTO 리스트와 다음 델타 링크
                
        Raises:
            GraphApiError: API 요청 실패 시
        """
        if processing_options is None:
            processing_options = EmailProcessingOptions()
            
        # 델타 링크 로드
        delta_key = f"{folder}_delta"
        delta_link = Config.get_delta_link(delta_key)
        
        if delta_link:
            # 기존 델타 링크가 있는 경우
            logger.debug(f"기존 델타 링크 사용: {delta_key}")
            response = requests.get(delta_link, headers=self._get_headers())
            
            if response.status_code != 200:
                # 델타 링크 만료 등으로 오류 발생 시 초기화
                logger.warning(f"델타 링크 오류 (상태 코드: {response.status_code}), 초기화 후 재시도")
                Config.reset_delta_link(delta_key)
                return self.get_delta_messages(folder, processing_options)
                
            data = response.json()
        else:
            # 새로운 델타 쿼리 시작
            url = self._build_message_url(folder)
            
            # 쿼리 파라미터 생성
            params = {
                "$delta": "",
                "$select": "id,subject,bodyPreview,body,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,isRead,importance,hasAttachments,conversationId,categories"
            }
            
            # API 요청
            data = self._make_request("GET", url, params=params)
        
        # 응답 처리
        return self._process_delta_response(data, delta_key, processing_options)
    
    def mark_as_read(self, message_id: str) -> bool:
        """메시지를 읽음으로 표시합니다.
        
        Args:
            message_id (str): 메시지 ID
            
        Returns:
            bool: 성공 여부
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        url = f"/me/messages/{message_id}"
        
        # 요청 본문
        body = {
            "isRead": True
        }
        
        # API 요청
        self._make_request("PATCH", url, json=body)
        logger.debug(f"메시지 읽음으로 표시됨: {message_id}")
        return True
    
    def send_message(self, email: EmailDto) -> bool:
        """메시지를 발송합니다.
        
        Args:
            email (EmailDto): 발송할 이메일
            
        Returns:
            bool: 성공 여부
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        url = "/me/sendMail"
        
        # 요청 본문
        body = {
            "message": email.to_dict(),
            "saveToSentItems": True
        }
        
        # API 요청
        self._make_request("POST", url, json=body)
        logger.debug(f"메시지 발송 완료: {email.subject}")
        return True
    
    def search_messages(
        self,
        search_term: str,
        folder: Optional[str] = None,
        processing_options: Optional[EmailProcessingOptions] = None
    ) -> List[EmailDto]:
        """메시지를 검색합니다.
        
        Args:
            search_term (str): 검색어
            folder (Optional[str], optional): 폴더. 기본값은 None.
            processing_options (Optional[EmailProcessingOptions], optional): 처리 옵션
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        if processing_options is None:
            processing_options = EmailProcessingOptions()
            
        # 검색 URL 생성
        if folder:
            url = f"/me/mailFolders/{folder}/messages"
        else:
            url = "/me/messages"
            
        # 쿼리 파라미터 생성
        params = {
            "$search": f'"{search_term}"',
            "$top": 50,
            "$select": "id,subject,bodyPreview,body,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,isRead,importance,hasAttachments,conversationId,categories"
        }
        
        # API 요청
        response = self._make_request("GET", url, params=params)
        
        # 응답 처리
        messages = response.get("value", [])
        logger.debug(f"검색 결과: {len(messages)}개의 메시지 찾음")
        
        # EmailDto 변환
        email_dtos = []
        
        for message in messages:
            email_dto = EmailDto.from_dict(message, processing_options)
            email_dtos.append(email_dto)
        
        return email_dtos
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        expand: Optional[str] = None
    ) -> Dict[str, Any]:
        """API 요청을 수행합니다.
        
        Args:
            method (str): HTTP 메소드
            endpoint (str): API 엔드포인트
            params (Optional[Dict[str, Any]], optional): 쿼리 파라미터
            json (Optional[Dict[str, Any]], optional): 요청 본문 (JSON)
            expand (Optional[str], optional): $expand 값
            
        Returns:
            Dict[str, Any]: API 응답
            
        Raises:
            GraphApiError: API 요청 실패 시
        """
        # URL 생성
        if endpoint.startswith(self.api_url):
            url = endpoint
        elif endpoint.startswith("/"):
            url = f"{self.api_url}{endpoint}"
        else:
            url = f"{self.api_url}/{endpoint}"
            
        # 토큰 조회
        token = self.auth_manager.get_token()
        
        if not token:
            error_msg = "API 요청을 위한 액세스 토큰이 없습니다. 먼저, 인증이 필요합니다."
            logger.error(error_msg)
            raise GraphApiError(error_msg)
            
        # 헤더 설정
        headers = self._get_headers(token.get("access_token"))
        
        # $expand 추가
        if expand:
            if params is None:
                params = {}
            params["$expand"] = expand
            
        try:
            # API 요청 수행
            logger.debug(f"API 요청: {method} {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, json=json)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, params=params, json=json)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메소드: {method}")
                
            # 응답 확인
            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                error_detail = error_data.get("error", {})
                
                error_msg = f"Graph API 오류 (상태 코드: {response.status_code}): {error_detail.get('message', 'Unknown error')}"
                logger.error(error_msg)
                
                raise GraphApiError(
                    error_msg,
                    status_code=response.status_code,
                    error_code=error_detail.get("code"),
                    request_id=response.headers.get("request-id")
                )
                
            # JSON 응답 파싱
            if response.text:
                return response.json()
            return {}
            
        except requests.RequestException as e:
            logger.exception("API 요청 중 네트워크 오류 발생")
            raise GraphApiError(f"API 요청 중 네트워크 오류 발생: {str(e)}")
            
        except json.JSONDecodeError as e:
            logger.exception("API 응답 JSON 파싱 오류 발생")
            raise GraphApiError(f"API 응답 JSON 파싱 오류 발생: {str(e)}")
            
        except GraphApiError:
            # 이미 로깅 및 변환된 오류
            raise
            
        except Exception as e:
            logger.exception("API 요청 중 예기치 않은 오류 발생")
            raise GraphApiError(f"API 요청 중 예기치 않은 오류 발생: {str(e)}")
    
    def _get_headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        """API 요청 헤더를 생성합니다.
        
        Args:
            access_token (Optional[str], optional): 액세스 토큰
            
        Returns:
            Dict[str, str]: 헤더 딕셔너리
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        return headers
    
    def _build_message_url(self, folder: str) -> str:
        """메시지 URL을 생성합니다.
        
        Args:
            folder (str): 폴더 (inbox, sentItems 등)
            
        Returns:
            str: 메시지 URL
        """
        if folder == "inbox":
            return "/me/mailFolders/inbox/messages"
        elif folder == "sentItems":
            return "/me/mailFolders/sentItems/messages"
        elif folder == "draft":
            return "/me/mailFolders/drafts/messages"
        else:
            return f"/me/mailFolders/{folder}/messages"
    
    def _process_delta_response(
        self,
        response: Dict[str, Any],
        delta_key: str,
        processing_options: EmailProcessingOptions
    ) -> Tuple[List[EmailDto], Optional[str]]:
        """델타 응답을 처리합니다.
        
        Args:
            response (Dict[str, Any]): API 응답
            delta_key (str): 델타 링크 키
            processing_options (EmailProcessingOptions): 처리 옵션
            
        Returns:
            Tuple[List[EmailDto], Optional[str]]: 
                이메일 DTO 리스트와 다음 델타 링크
                
        Raises:
            DeltaLinkError: 델타 링크 처리 오류 시
        """
        try:
            # 메시지 변환
            messages = response.get("value", [])
            logger.debug(f"델타 쿼리 결과: {len(messages)}개의 변경사항")
            
            # EmailDto 변환
            email_dtos = []
            
            for message in messages:
                # 삭제된 메시지 처리
                if "@removed" in message:
                    # 삭제 이벤트는 현재 처리하지 않음
                    continue
                    
                # DTO 변환
                email_dto = EmailDto.from_dict(message, processing_options)
                email_dtos.append(email_dto)
            
            # 다음 델타 링크 추출
            next_link = None
            
            if "@odata.nextLink" in response:
                next_link = response["@odata.nextLink"]
                
            if "@odata.deltaLink" in response:
                delta_link = response["@odata.deltaLink"]
                
                # 델타 링크 저장
                Config.save_delta_link(delta_key, delta_link)
                logger.debug(f"델타 링크 저장됨: {delta_key}")
                
                next_link = delta_link
            
            return email_dtos, next_link
            
        except Exception as e:
            logger.exception("델타 응답 처리 중 오류 발생")
            raise DeltaLinkError(f"델타 응답 처리 중 오류 발생: {str(e)}")
