"""이메일 관련 스키마 모듈

이 모듈은 이메일 관련 데이터 클래스를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


@dataclass
class EmailParticipant:
    """이메일 참여자 클래스
    
    이메일 발신자 또는 수신자 정보를 포함하는 데이터 클래스입니다.
    
    Attributes:
        email (str): 이메일 주소
        name (str): 표시 이름
        type (str): 참여자 유형 ('from', 'to', 'cc', 'bcc')
    """
    
    email: str
    name: str = ""
    type: str = "to"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], participant_type: str = "to") -> 'EmailParticipant':
        """딕셔너리에서 EmailParticipant 객체를 생성합니다.
        
        Args:
            data (Dict[str, Any]): 참여자 정보가 포함된 딕셔너리
            participant_type (str, optional): 참여자 유형. 기본값은 "to".
            
        Returns:
            EmailParticipant: 생성된 EmailParticipant 객체
        """
        email_address = data.get("emailAddress", {})
        return cls(
            email=email_address.get("address", ""),
            name=email_address.get("name", ""),
            type=participant_type
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """EmailParticipant 객체를 딕셔너리로 변환합니다.
        
        Returns:
            Dict[str, Any]: 변환된 딕셔너리
        """
        return {
            "emailAddress": {
                "address": self.email,
                "name": self.name
            }
        }


@dataclass
class EmailFilter:
    """이메일 필터 클래스
    
    이메일 필터링 옵션을 포함하는 데이터 클래스입니다.
    
    Attributes:
        start_date (Optional[Union[datetime, str]]): 시작 날짜 (datetime 객체 또는 ISO 8601 형식 문자열)
        end_date (Optional[Union[datetime, str]]): 종료 날짜 (datetime 객체 또는 ISO 8601 형식 문자열)
        folder (Optional[str]): 폴더 (예: 'inbox', 'sentItems')
        limit (int): 최대 결과 수
        search_query (Optional[str]): 검색 쿼리
        exclude_senders (List[str]): 제외할 발신자 목록
        only_unread (bool): 읽지 않은 메일만 포함할지 여부
    """
    
    start_date: Optional[Union[datetime, str]] = None
    end_date: Optional[Union[datetime, str]] = None
    folder: Optional[str] = None
    limit: int = 50
    search_query: Optional[str] = None
    exclude_senders: List[str] = field(default_factory=list)
    only_unread: bool = False
    
    def get_filter_query(self) -> Optional[str]:
        """OData 필터 쿼리를 생성합니다.
        
        Returns:
            Optional[str]: OData 필터 쿼리 문자열, 필터가 없으면 None
        """
        filters = []
        
        # 날짜 필터
        if self.start_date:
            # 문자열 또는 datetime 객체 처리
            if isinstance(self.start_date, str):
                # 이미 문자열이면 그대로 사용
                start_date_str = self.start_date
            else:
                # datetime 객체면 ISO 형식으로 변환
                start_date_str = self.start_date.isoformat()
                # 이미 타임존 정보가 있으면 그대로 사용, 없으면 Z 추가
                if start_date_str.endswith('+00:00'):
                    start_date_str = start_date_str.replace('+00:00', 'Z')
                elif '+' not in start_date_str and '-' not in start_date_str[10:]:
                    start_date_str += 'Z'
                
            if self.folder == "sentItems":
                filters.append(f"sentDateTime ge {start_date_str}")
            else:
                filters.append(f"receivedDateTime ge {start_date_str}")
        
        if self.end_date:
            # 문자열 또는 datetime 객체 처리
            if isinstance(self.end_date, str):
                # 이미 문자열이면 그대로 사용
                end_date_str = self.end_date
            else:
                # datetime 객체면 ISO 형식으로 변환
                end_date_str = self.end_date.isoformat()
                # 이미 타임존 정보가 있으면 그대로 사용, 없으면 Z 추가
                if end_date_str.endswith('+00:00'):
                    end_date_str = end_date_str.replace('+00:00', 'Z')
                elif '+' not in end_date_str and '-' not in end_date_str[10:]:
                    end_date_str += 'Z'
                
            if self.folder == "sentItems":
                filters.append(f"sentDateTime le {end_date_str}")
            else:
                filters.append(f"receivedDateTime le {end_date_str}")
        
        # 읽지 않은 메일만 필터링
        if self.only_unread:
            filters.append("isRead eq false")
        
        if not filters:
            return None
            
        return " and ".join(filters)
    
    def should_exclude_sender(self, email: str, name: str) -> bool:
        """발신자를 제외할지 여부를 결정합니다.
        
        Args:
            email (str): 발신자 이메일
            name (str): 발신자 이름
            
        Returns:
            bool: 제외해야 하면 True, 아니면 False
        """
        for exclude in self.exclude_senders:
            if exclude.lower() in email.lower() or exclude.lower() in name.lower():
                return True
        return False


@dataclass
class EmailProcessingOptions:
    """이메일 처리 옵션 클래스
    
    이메일 처리 방법을 정의하는 데이터 클래스입니다.
    
    Attributes:
        convert_html_to_text (bool): HTML 본문을 텍스트로 변환할지 여부
        apply_filters (bool): 필터를 적용할지 여부
        include_body (bool): 본문을 포함할지 여부
        include_attachments (bool): 첨부 파일을 포함할지 여부
    """
    
    convert_html_to_text: bool = True
    apply_filters: bool = True
    include_body: bool = True
    include_attachments: bool = False


@dataclass
class EmailAttachment:
    """이메일 첨부 파일 클래스
    
    이메일 첨부 파일 정보를 포함하는 데이터 클래스입니다.
    
    Attributes:
        id (str): 첨부 파일 ID
        name (str): 파일 이름
        content_type (str): 콘텐츠 유형 (MIME 타입)
        size (int): 파일 크기 (바이트)
        is_inline (bool): 인라인 첨부 파일 여부
        content_id (Optional[str]): 콘텐츠 ID (인라인 첨부 파일용)
        content (Optional[bytes]): 파일 내용 (로드된 경우)
    """
    
    id: str
    name: str
    content_type: str
    size: int
    is_inline: bool = False
    content_id: Optional[str] = None
    content: Optional[bytes] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailAttachment':
        """딕셔너리에서 EmailAttachment 객체를 생성합니다.
        
        Args:
            data (Dict[str, Any]): 첨부 파일 정보가 포함된 딕셔너리
            
        Returns:
            EmailAttachment: 생성된 EmailAttachment 객체
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            content_type=data.get("contentType", ""),
            size=data.get("size", 0),
            is_inline=data.get("isInline", False),
            content_id=data.get("contentId")
        )


@dataclass
class EmailDto:
    """이메일 데이터 전송 객체 클래스
    
    이메일 정보를 포함하는 데이터 전송 객체(DTO)입니다.
    
    Attributes:
        id (str): 이메일 ID
        subject (str): 제목
        body_content (str): 본문 내용
        body_type (str): 본문 유형 ('html' 또는 'text')
        sender (EmailParticipant): 발신자
        recipients (List[EmailParticipant]): 수신자 목록
        cc_recipients (List[EmailParticipant]): 참조 수신자 목록
        bcc_recipients (List[EmailParticipant]): 숨은 참조 수신자 목록
        received_date (Optional[datetime]): 수신 날짜
        sent_date (Optional[datetime]): 발신 날짜
        is_read (bool): 읽음 여부
        importance (str): 중요도 ('low', 'normal', 'high')
        has_attachments (bool): 첨부 파일 여부
        attachments (List[EmailAttachment]): 첨부 파일 목록
        conversation_id (Optional[str]): 대화 ID
        categories (List[str]): 범주 목록
        raw_data (Dict[str, Any]): 원본 데이터
    """
    
    id: str
    subject: str
    body_content: str
    body_type: str
    sender: EmailParticipant
    recipients: List[EmailParticipant] = field(default_factory=list)
    cc_recipients: List[EmailParticipant] = field(default_factory=list)
    bcc_recipients: List[EmailParticipant] = field(default_factory=list)
    received_date: Optional[datetime] = None
    sent_date: Optional[datetime] = None
    is_read: bool = False
    importance: str = "normal"
    has_attachments: bool = False
    attachments: List[EmailAttachment] = field(default_factory=list)
    conversation_id: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], processing_options: EmailProcessingOptions = None) -> 'EmailDto':
        """딕셔너리에서 EmailDto 객체를 생성합니다.
        
        Args:
            data (Dict[str, Any]): 이메일 정보가 포함된 딕셔너리
            processing_options (EmailProcessingOptions, optional): 처리 옵션
            
        Returns:
            EmailDto: 생성된 EmailDto 객체
        """
        if processing_options is None:
            processing_options = EmailProcessingOptions()
            
        # 본문 처리
        body = data.get("body", {})
        body_content = body.get("content", "")
        body_type = body.get("contentType", "").lower()
        
        # HTML을 텍스트로 변환
        if processing_options.convert_html_to_text and body_type == "html":
            try:
                import html2text
                import re
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                body_content = h.handle(body_content)
                
                # html2text가 생성한 마크다운을 일반 텍스트로 변환하는 처리
                
                # 1단계: HTML 태그 정리
                # HTML 링크 태그를 텍스트로 변환
                body_content = re.sub(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', r'\2 (\1)', body_content, flags=re.IGNORECASE|re.DOTALL)
                # 나머지 HTML 태그 제거
                body_content = re.sub(r'<[^>]+>', '', body_content)
                
                # 2단계: 마크다운 서식 제거
                # 표 형식 제거 (|와 -, --------- 등)
                body_content = re.sub(r'\|[\s\|]*\n[-]{3,}[\s\n]*', '', body_content)
                body_content = re.sub(r'[-]{3,}', '', body_content)
                body_content = re.sub(r'\|[\s\|]*', '', body_content)
                
                # 수평선 제거 (*, -, _)
                body_content = re.sub(r'[\*\s]{3,}', '', body_content)
                body_content = re.sub(r'[_\s]{3,}', '', body_content)
                
                # 이스케이프 문자 제거
                body_content = re.sub(r'\\+\s*\\+', '', body_content)
                body_content = re.sub(r'\\+\s+', ' ', body_content)
                body_content = re.sub(r'\\+([^\s])', r'\1', body_content)
                
                # 마크다운 링크 정리 [텍스트](URL) -> 텍스트 (URL)
                body_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', body_content)
                
                # 강조 표시 제거
                body_content = re.sub(r'\*\*([^*]+)\*\*', r'\1', body_content)  # 굵은 글씨 (**text**)
                body_content = re.sub(r'\*([^*]+)\*', r'\1', body_content)      # 기울임 글씨 (*text*)
                body_content = re.sub(r'__([^_]+)__', r'\1', body_content)      # 굵은 글씨 (__text__)
                body_content = re.sub(r'_([^_]+)_', r'\1', body_content)        # 기울임 글씨 (_text_)
                body_content = re.sub(r'`([^`]+)`', r'\1', body_content)        # 인라인 코드
                
                # 3단계: 텍스트 가독성 개선
                # 연속된 공백 처리
                body_content = re.sub(r' {2,}', ' ', body_content)
                body_content = re.sub(r'\n{3,}', '\n\n', body_content)
                
                # 문장 구분을 위한 줄바꿈 추가
                body_content = re.sub(r'([.!?])\s+([A-Z가-힣])', r'\1\n\2', body_content)
                
                # 4단계: 단어 사이 공백 처리 (URL/이메일 제외)
                # 카멜케이스 처리 (소문자 + 대문자)
                body_content = re.sub(r'([a-z])([A-Z])', r'\1 \2', body_content)
                
                # 단어가 붙어있는 경우 분리
                # 'atestemail'과 같이 붙어있는 영어 단어 분리
                body_content = re.sub(r'([a-z]{2,})([A-Z][a-z]{2,})', r'\1 \2', body_content)  
                
                # 5단계: 특수한 경우 처리
                # URL이나 이메일에 공백이 들어간 경우 수정
                # http://... 또는 https://... 형식의 URL 인식
                body_content = re.sub(r'(https?:\/\/[^\s]+)\s+([^\s]+)', r'\1\2', body_content)
                # 이메일 주소 내 공백 제거
                body_content = re.sub(r'([a-zA-Z0-9._%+-]+)\s+@\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1@\2', body_content)
                
                # 문장, 구 사이의 공백 처리 개선
                body_content = re.sub(r'([.!?])([A-Z가-힣])', r'\1 \2', body_content)  # 문장 부호 후 공백
                body_content = re.sub(r'(\))([A-Z가-힣a-z])', r'\1 \2', body_content)  # 괄호 후 공백
                
                # 앞뒤 공백 제거
                body_content = body_content.strip()
                
                body_type = "text"
            except ImportError:
                # html2text가 설치되지 않은 경우
                pass
        
        # 발신자 처리
        sender = data.get("from", {}).get("emailAddress", {})
        sender_participant = EmailParticipant(
            email=sender.get("address", ""),
            name=sender.get("name", ""),
            type="from"
        )
        
        # 수신 날짜 및 발신 날짜 처리
        received_date = None
        if "receivedDateTime" in data:
            received_date = datetime.fromisoformat(data["receivedDateTime"].replace("Z", "+00:00"))
            
        sent_date = None
        if "sentDateTime" in data:
            sent_date = datetime.fromisoformat(data["sentDateTime"].replace("Z", "+00:00"))
        
        # 수신자 처리
        recipients = []
        for recipient_data in data.get("toRecipients", []):
            recipients.append(EmailParticipant.from_dict(recipient_data, "to"))
            
        cc_recipients = []
        for cc_data in data.get("ccRecipients", []):
            cc_recipients.append(EmailParticipant.from_dict(cc_data, "cc"))
            
        bcc_recipients = []
        for bcc_data in data.get("bccRecipients", []):
            bcc_recipients.append(EmailParticipant.from_dict(bcc_data, "bcc"))
        
        # 첨부 파일 처리
        has_attachments = data.get("hasAttachments", False)
        attachments = []
        
        if processing_options.include_attachments and has_attachments:
            for attachment_data in data.get("attachments", []):
                attachments.append(EmailAttachment.from_dict(attachment_data))
        
        return cls(
            id=data.get("id", ""),
            subject=data.get("subject", "(제목 없음)"),
            body_content=body_content,
            body_type=body_type,
            sender=sender_participant,
            recipients=recipients,
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            received_date=received_date,
            sent_date=sent_date,
            is_read=data.get("isRead", False),
            importance=data.get("importance", "normal"),
            has_attachments=has_attachments,
            attachments=attachments,
            conversation_id=data.get("conversationId"),
            categories=data.get("categories", []),
            raw_data=data
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """EmailDto 객체를 딕셔너리로 변환합니다.
        (Graph API 요청 본문에 사용할 수 있는 형식)
        
        Returns:
            Dict[str, Any]: 변환된 딕셔너리
        """
        result = {
            "subject": self.subject,
            "body": {
                "contentType": self.body_type,
                "content": self.body_content
            },
            "toRecipients": [recipient.to_dict() for recipient in self.recipients],
            "importance": self.importance
        }
        
        if self.cc_recipients:
            result["ccRecipients"] = [recipient.to_dict() for recipient in self.cc_recipients]
            
        if self.bcc_recipients:
            result["bccRecipients"] = [recipient.to_dict() for recipient in self.bcc_recipients]
            
        return result
