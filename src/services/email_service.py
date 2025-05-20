"""이메일 서비스 모듈

이 모듈은 이메일 관련 비즈니스 로직을 제공합니다.
"""

from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime, timedelta

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import EmailProcessingError, GraphApiError
from src.infra.config import Config
from src.infra.graph_gateway import GraphApiGateway
from src.schemas.email import EmailDto, EmailFilter, EmailProcessingOptions


# 로거 설정
logger = LoggerFactory.get_logger(__name__)


class EmailService:
    """이메일 서비스 클래스
    
    이메일 관련 비즈니스 로직을 제공합니다.
    """
    
    def __init__(self):
        """초기화 메소드"""
        self.graph_gateway = GraphApiGateway()
        logger.debug("EmailService 초기화 완료")
    
    def get_inbox_emails(
        self, 
        days: Optional[int] = None,
        limit: Optional[int] = None,
        filter_senders: bool = True
    ) -> List[EmailDto]:
        """수신함 이메일 목록을 조회합니다. (본문 제외)
        
        Args:
            days (Optional[int], optional): 조회할 일수. 기본값은 None.
            limit (Optional[int], optional): 최대 결과 수. 기본값은 None.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 제외)
            processing_options = EmailProcessingOptions(
                include_body=False,
                apply_filters=filter_senders
            )
                
            # 필터 옵션 설정
            filter_options = EmailFilter(
                folder="inbox",
                limit=limit or Config.DEFAULT_LIMIT,
                exclude_senders=Config.get_filter_senders() if filter_senders else []
            )
            
            # 날짜 필터 설정
            if days is not None:
                filter_options.start_date = datetime.now() - timedelta(days=days)
                
            logger.debug(f"수신함 이메일 목록 조회: {days}일, 최대 {filter_options.limit}개")
            
            # 메시지 조회
            emails = self.graph_gateway.get_messages(filter_options, processing_options)
            
            logger.info(f"수신함 이메일 목록 조회 완료: {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"이메일 조회 중 오류 발생: {str(e)}")
    
    def get_sent_emails(
        self, 
        days: Optional[int] = None,
        limit: Optional[int] = None,
        filter_senders: bool = True
    ) -> List[EmailDto]:
        """송신함 이메일 목록을 조회합니다. (본문 제외)
        
        Args:
            days (Optional[int], optional): 조회할 일수. 기본값은 None.
            limit (Optional[int], optional): 최대 결과 수. 기본값은 None.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 제외)
            processing_options = EmailProcessingOptions(
                include_body=False,
                apply_filters=filter_senders
            )
                
            # 필터 옵션 설정
            filter_options = EmailFilter(
                folder="sentItems",
                limit=limit or Config.DEFAULT_LIMIT,
                exclude_senders=Config.get_filter_senders() if filter_senders else []
            )
            
            # 날짜 필터 설정
            if days is not None:
                filter_options.start_date = datetime.now() - timedelta(days=days)
                
            logger.debug(f"송신함 이메일 목록 조회: {days}일, 최대 {filter_options.limit}개")
            
            # 메시지 조회
            emails = self.graph_gateway.get_messages(filter_options, processing_options)
            
            logger.info(f"송신함 이메일 목록 조회 완료: {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"이메일 조회 중 오류 발생: {str(e)}")
    
    def get_all_emails(
        self, 
        days: Optional[int] = None,
        limit: Optional[int] = None,
        filter_senders: bool = True
    ) -> Dict[str, List[EmailDto]]:
        """모든 이메일(수신함, 송신함) 목록을 조회합니다. (본문 제외)
        
        Args:
            days (Optional[int], optional): 조회할 일수. 기본값은 None.
            limit (Optional[int], optional): 최대 결과 수. 기본값은 None.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            
        Returns:
            Dict[str, List[EmailDto]]: 폴더별 이메일 DTO 리스트
                {'inbox': [...], 'sentItems': [...]}
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 각 폴더별로 이메일 조회
            inbox_emails = self.get_inbox_emails(days, limit, filter_senders)
            sent_emails = self.get_sent_emails(days, limit, filter_senders)
            
            # 결과 합치기
            return {
                'inbox': inbox_emails,
                'sentItems': sent_emails
            }
            
        except Exception as e:
            # 오류 처리
            logger.exception("모든 이메일 조회 중 오류 발생")
            if isinstance(e, (EmailProcessingError, GraphApiError)):
                raise
            raise EmailProcessingError(f"모든 이메일 조회 중 오류 발생: {str(e)}")
    
    def get_inbox_emails_with_body(
        self, 
        start_date: Optional[Union[datetime, str]] = None,
        end_date: Optional[Union[datetime, str]] = None,
        days: Optional[int] = None,
        limit: int = 1000,
        filter_senders: bool = True,
        convert_html_to_text: bool = True
    ) -> List[EmailDto]:
        """수신함 이메일을 본문과 함께 조회합니다.
        
        Args:
            start_date (Optional[Union[datetime, str]], optional): 조회 시작 날짜.
                datetime 객체 또는 ISO 8601 형식 문자열(예: '2025-03-01T00:00:00Z'). 기본값은 None.
            end_date (Optional[Union[datetime, str]], optional): 조회 종료 날짜.
                datetime 객체 또는 ISO 8601 형식 문자열(예: '2025-03-11T23:59:59Z'). 기본값은 None.
            days (Optional[int], optional): 조회할 일수 (start_date가 None일 경우에만 사용). 기본값은 None.
            limit (int, optional): 최대 결과 수. 기본값은 1000.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            convert_html_to_text (bool, optional): HTML 본문을 텍스트로 변환할지 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트 (본문 포함)
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 포함)
            processing_options = EmailProcessingOptions(
                include_body=True,
                apply_filters=filter_senders,
                convert_html_to_text=convert_html_to_text
            )
                
            # 필터 옵션 설정
            filter_options = EmailFilter(
                folder="inbox",
                limit=limit,
                exclude_senders=Config.get_filter_senders() if filter_senders else []
            )
            
            # 날짜 필터 설정 (우선순위: 직접 지정된 날짜 > days 파라미터)
            if start_date is not None:
                filter_options.start_date = start_date
            elif days is not None:
                filter_options.start_date = datetime.now() - timedelta(days=days)
                
            if end_date is not None:
                filter_options.end_date = end_date
                
            logger.debug(f"수신함 이메일 조회 (본문 포함): {days}일, 최대 {filter_options.limit}개")
            
            # 메시지 조회
            emails = self.graph_gateway.get_messages(filter_options, processing_options)
            
            logger.info(f"수신함 이메일 조회 완료 (본문 포함): {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"이메일 조회 중 오류 발생: {str(e)}")
            
    def get_sent_emails_with_body(
        self, 
        start_date: Optional[Union[datetime, str]] = None,
        end_date: Optional[Union[datetime, str]] = None,
        days: Optional[int] = None,
        limit: int = 1000,
        filter_senders: bool = True,
        convert_html_to_text: bool = True
    ) -> List[EmailDto]:
        """송신함 이메일을 본문과 함께 조회합니다.
        
        Args:
            start_date (Optional[Union[datetime, str]], optional): 조회 시작 날짜.
                datetime 객체 또는 ISO 8601 형식 문자열(예: '2025-03-01T00:00:00Z'). 기본값은 None.
            end_date (Optional[Union[datetime, str]], optional): 조회 종료 날짜.
                datetime 객체 또는 ISO 8601 형식 문자열(예: '2025-03-11T23:59:59Z'). 기본값은 None.
            days (Optional[int], optional): 조회할 일수 (start_date가 None일 경우에만 사용). 기본값은 None.
            limit (int, optional): 최대 결과 수. 기본값은 1000.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            convert_html_to_text (bool, optional): HTML 본문을 텍스트로 변환할지 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트 (본문 포함)
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 포함)
            processing_options = EmailProcessingOptions(
                include_body=True,
                apply_filters=filter_senders,
                convert_html_to_text=convert_html_to_text
            )
                
            # 필터 옵션 설정
            filter_options = EmailFilter(
                folder="sentItems",
                limit=limit,
                exclude_senders=Config.get_filter_senders() if filter_senders else []
            )
            
            # 날짜 필터 설정 (우선순위: 직접 지정된 날짜 > days 파라미터)
            if start_date is not None:
                filter_options.start_date = start_date
            elif days is not None:
                filter_options.start_date = datetime.now() - timedelta(days=days)
                
            if end_date is not None:
                filter_options.end_date = end_date
                
            logger.debug(f"송신함 이메일 조회 (본문 포함): {days}일, 최대 {filter_options.limit}개")
            
            # 메시지 조회
            emails = self.graph_gateway.get_messages(filter_options, processing_options)
            
            logger.info(f"송신함 이메일 조회 완료 (본문 포함): {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"이메일 조회 중 오류 발생: {str(e)}")
            
    def get_all_emails_with_body(
        self, 
        start_date: Optional[Union[datetime, str]] = None,
        end_date: Optional[Union[datetime, str]] = None,
        days: Optional[int] = None,
        limit: int = 1000,
        filter_senders: bool = True,
        convert_html_to_text: bool = True
    ) -> Dict[str, List[EmailDto]]:
        """모든 이메일(수신함, 송신함)을 본문과 함께 조회합니다.
        
        Args:
            start_date (Optional[Union[datetime, str]], optional): 조회 시작 날짜.
                datetime 객체 또는 ISO 8601 형식 문자열(예: '2025-03-01T00:00:00Z'). 기본값은 None.
            end_date (Optional[Union[datetime, str]], optional): 조회 종료 날짜.
                datetime 객체 또는 ISO 8601 형식 문자열(예: '2025-03-11T23:59:59Z'). 기본값은 None.
            days (Optional[int], optional): 조회할 일수 (start_date가 None일 경우에만 사용). 기본값은 None.
            limit (int, optional): 최대 결과 수. 기본값은 1000.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            convert_html_to_text (bool, optional): HTML 본문을 텍스트로 변환할지 여부. 기본값은 True.
            
        Returns:
            Dict[str, List[EmailDto]]: 폴더별 이메일 DTO 리스트 (본문 포함)
                {'inbox': [...], 'sentItems': [...]}
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 각 폴더별로 이메일 조회
            inbox_emails = self.get_inbox_emails_with_body(
                start_date=start_date,
                end_date=end_date,
                days=days,
                limit=limit,
                filter_senders=filter_senders,
                convert_html_to_text=convert_html_to_text
            )
            
            sent_emails = self.get_sent_emails_with_body(
                start_date=start_date,
                end_date=end_date,
                days=days,
                limit=limit,
                filter_senders=filter_senders,
                convert_html_to_text=convert_html_to_text
            )
            
            # 결과 합치기
            return {
                'inbox': inbox_emails,
                'sentItems': sent_emails
            }
            
        except Exception as e:
            # 오류 처리
            logger.exception("모든 이메일 조회 중 오류 발생")
            if isinstance(e, (EmailProcessingError, GraphApiError)):
                raise
            raise EmailProcessingError(f"모든 이메일 조회 중 오류 발생: {str(e)}")
    
    def get_delta_emails(
        self,
        folder: str = "inbox",
        filter_senders: bool = True
    ) -> List[EmailDto]:
        """델타 쿼리로 변경된 이메일 목록을 조회합니다. (본문 제외)
        
        Args:
            folder (str, optional): 폴더. 기본값은 "inbox".
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 제외)
            processing_options = EmailProcessingOptions(
                include_body=False,
                apply_filters=filter_senders
            )
                
            logger.debug(f"델타 쿼리 이메일 목록 조회: {folder}")
            
            # 델타 쿼리 요청
            emails, next_link = self.graph_gateway.get_delta_messages(folder, processing_options)
            
            logger.info(f"델타 쿼리 이메일 목록 조회 완료: {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("델타 쿼리 이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"델타 쿼리 이메일 조회 중 오류 발생: {str(e)}")
            
    def get_delta_emails_with_body(
        self,
        folder: str = "inbox",
        filter_senders: bool = True,
        convert_html_to_text: bool = True
    ) -> List[EmailDto]:
        """델타 쿼리로 변경된 이메일을 본문과 함께 조회합니다.
        
        Args:
            folder (str, optional): 폴더. 기본값은 "inbox".
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            convert_html_to_text (bool, optional): HTML 본문을 텍스트로 변환할지 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트 (본문 포함)
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 포함)
            processing_options = EmailProcessingOptions(
                include_body=True,
                apply_filters=filter_senders,
                convert_html_to_text=convert_html_to_text
            )
                
            logger.debug(f"델타 쿼리 이메일 조회 (본문 포함): {folder}")
            
            # 델타 쿼리 요청
            emails, next_link = self.graph_gateway.get_delta_messages(folder, processing_options)
            
            logger.info(f"델타 쿼리 이메일 조회 완료 (본문 포함): {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("델타 쿼리 이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"델타 쿼리 이메일 조회 중 오류 발생: {str(e)}")
    
    def search_emails(
        self,
        search_term: str,
        folder: Optional[str] = None,
        filter_senders: bool = True
    ) -> List[EmailDto]:
        """이메일 목록을 검색합니다. (본문 제외)
        
        Args:
            search_term (str): 검색어
            folder (Optional[str], optional): 폴더. 기본값은 None.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 제외)
            processing_options = EmailProcessingOptions(
                include_body=False,
                apply_filters=filter_senders
            )
                
            logger.debug(f"이메일 목록 검색: '{search_term}', 폴더: {folder or '전체'}")
            
            # 검색 요청
            emails = self.graph_gateway.search_messages(search_term, folder, processing_options)
            
            logger.info(f"이메일 목록 검색 완료: {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 검색 중 오류 발생")
            raise EmailProcessingError(f"이메일 검색 중 오류 발생: {str(e)}")
    
    def search_emails_with_body(
        self,
        search_term: str,
        folder: Optional[str] = None,
        filter_senders: bool = True,
        convert_html_to_text: bool = True
    ) -> List[EmailDto]:
        """이메일을 본문과 함께 검색합니다.
        
        Args:
            search_term (str): 검색어
            folder (Optional[str], optional): 폴더. 기본값은 None.
            filter_senders (bool, optional): 발신자 필터링 적용 여부. 기본값은 True.
            convert_html_to_text (bool, optional): HTML 본문을 텍스트로 변환할지 여부. 기본값은 True.
            
        Returns:
            List[EmailDto]: 이메일 DTO 리스트 (본문 포함)
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정 (본문 포함)
            processing_options = EmailProcessingOptions(
                include_body=True,
                apply_filters=filter_senders,
                convert_html_to_text=convert_html_to_text
            )
                
            logger.debug(f"이메일 검색 (본문 포함): '{search_term}', 폴더: {folder or '전체'}")
            
            # 검색 요청
            emails = self.graph_gateway.search_messages(search_term, folder, processing_options)
            
            logger.info(f"이메일 검색 완료 (본문 포함): {len(emails)}개")
            return emails
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 검색 중 오류 발생")
            raise EmailProcessingError(f"이메일 검색 중 오류 발생: {str(e)}")
    
    def send_email(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        cc_recipients: Optional[List[str]] = None,
        bcc_recipients: Optional[List[str]] = None,
        body_type: str = "html",
        importance: str = "normal"
    ) -> bool:
        """이메일을 발송합니다.
        
        Args:
            subject (str): 제목
            body (str): 본문
            recipients (List[str]): 수신자 목록
            cc_recipients (Optional[List[str]], optional): 참조 수신자 목록. 기본값은 None.
            bcc_recipients (Optional[List[str]], optional): 숨은 참조 수신자 목록. 기본값은 None.
            body_type (str, optional): 본문 유형 ('html' 또는 'text'). 기본값은 "html".
            importance (str, optional): 중요도 ('low', 'normal', 'high'). 기본값은 "normal".
            
        Returns:
            bool: 발송 성공 여부
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        from src.schemas.email import EmailParticipant
        
        try:
            # 수신자 목록 변환
            to_recipients = []
            for email in recipients:
                name = email.split('@')[0] if '@' in email else email
                to_recipients.append(EmailParticipant(email=email, name=name, type="to"))
                
            # 참조 수신자 목록 변환
            cc_list = []
            if cc_recipients:
                for email in cc_recipients:
                    name = email.split('@')[0] if '@' in email else email
                    cc_list.append(EmailParticipant(email=email, name=name, type="cc"))
                    
            # 숨은 참조 수신자 목록 변환
            bcc_list = []
            if bcc_recipients:
                for email in bcc_recipients:
                    name = email.split('@')[0] if '@' in email else email
                    bcc_list.append(EmailParticipant(email=email, name=name, type="bcc"))
            
            # 발신자 정보는 사용하지 않음 (현재 인증된 사용자가 발신자가 됨)
            sender = EmailParticipant(email="", name="", type="from")
            
            # 이메일 DTO 생성
            email = EmailDto(
                id="",  # 발송 시에는 ID 필요 없음
                subject=subject,
                body_content=body,
                body_type=body_type,
                sender=sender,
                recipients=to_recipients,
                cc_recipients=cc_list,
                bcc_recipients=bcc_list,
                importance=importance
            )
            
            logger.debug(f"이메일 발송: '{subject}', 수신자 {len(to_recipients)}명")
            
            # 발송 요청
            result = self.graph_gateway.send_message(email)
            
            logger.info(f"이메일 발송 완료: '{subject}'")
            return result
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 발송 중 오류 발생")
            raise EmailProcessingError(f"이메일 발송 중 오류 발생: {str(e)}")
    
    def get_email(
        self,
        message_id: str,
        include_attachments: bool = False
    ) -> EmailDto:
        """특정 이메일을 조회합니다.
        
        Args:
            message_id (str): 메시지 ID
            include_attachments (bool, optional): 첨부 파일 포함 여부. 기본값은 False.
            
        Returns:
            EmailDto: 이메일 DTO
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            # 처리 옵션 설정
            processing_options = EmailProcessingOptions(
                include_attachments=include_attachments
            )
                
            logger.debug(f"이메일 조회: ID={message_id}, 첨부파일 포함={include_attachments}")
            
            # 메시지 조회
            email = self.graph_gateway.get_message(message_id, processing_options)
            
            logger.info(f"이메일 조회 완료: ID={message_id}")
            return email
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 조회 중 오류 발생")
            raise EmailProcessingError(f"이메일 조회 중 오류 발생: {str(e)}")
    
    def mark_as_read(self, message_id: str) -> bool:
        """이메일을 읽음으로 표시합니다.
        
        Args:
            message_id (str): 메시지 ID
            
        Returns:
            bool: 성공 여부
            
        Raises:
            EmailProcessingError: 이메일 처리 오류 시
            GraphApiError: Graph API 요청 실패 시
        """
        try:
            logger.debug(f"이메일 읽음 표시: ID={message_id}")
            
            # 읽음 표시 요청
            result = self.graph_gateway.mark_as_read(message_id)
            
            logger.info(f"이메일 읽음 표시 완료: ID={message_id}")
            return result
            
        except GraphApiError as e:
            # Graph API 오류는 그대로 전파
            raise
            
        except Exception as e:
            # 기타 오류는 EmailProcessingError로 변환
            logger.exception("이메일 읽음 표시 중 오류 발생")
            raise EmailProcessingError(f"이메일 읽음 표시 중 오류 발생: {str(e)}")
    
    def add_filter_sender(self, sender: str) -> None:
        """필터링할 발신자를 추가합니다.
        
        Args:
            sender (str): 추가할 발신자
        """
        Config.add_filter_sender(sender)
        logger.info(f"필터링할 발신자 추가됨: {sender}")
    
    def remove_filter_sender(self, sender: str) -> bool:
        """필터링할 발신자를 제거합니다.
        
        Args:
            sender (str): 제거할 발신자
            
        Returns:
            bool: 제거 성공 여부
        """
        result = Config.remove_filter_sender(sender)
        if result:
            logger.info(f"필터링할 발신자 제거됨: {sender}")
        else:
            logger.warning(f"필터링할 발신자 제거 실패 (없음): {sender}")
        return result
    
    def get_filter_senders(self) -> List[str]:
        """필터링할 발신자 목록을 반환합니다.
        
        Returns:
            List[str]: 필터링할 발신자 목록
        """
        return Config.get_filter_senders()
