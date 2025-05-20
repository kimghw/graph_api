"""인증 관련 스키마 모듈

이 모듈은 인증 관련 데이터 클래스를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class TokenCredential:
    """토큰 자격 증명 클래스
    
    인증 토큰 정보를 포함하는 데이터 클래스입니다.
    
    Attributes:
        access_token (str): 액세스 토큰
        token_type (str): 토큰 유형 (일반적으로 "Bearer")
        expires_in (int): 만료 시간(초)
        ext_expires_in (int): 확장 만료 시간(초)
        refresh_token (Optional[str]): 갱신 토큰 (없을 수 있음)
        scope (str): 권한 범위
        id_token (Optional[str]): ID 토큰 (없을 수 있음)
        expires_at (datetime): 만료 일시
    """
    
    access_token: str
    token_type: str
    expires_in: int
    ext_expires_in: int
    refresh_token: Optional[str] = None
    scope: str = ""
    id_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenCredential':
        """딕셔너리에서 TokenCredential 객체를 생성합니다.
        
        Args:
            data (Dict[str, Any]): 토큰 정보가 포함된 딕셔너리
            
        Returns:
            TokenCredential: 생성된 TokenCredential 객체
        """
        token = cls(
            access_token=data.get("access_token", ""),
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in", 0),
            ext_expires_in=data.get("ext_expires_in", 0),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope", ""),
            id_token=data.get("id_token")
        )
        
        # 만료 시간 계산
        if 'expires_on' in data:
            # Unix timestamp로 제공된 경우
            token.expires_at = datetime.fromtimestamp(data['expires_on'])
        else:
            # MSAL 응답에는 일반적으로 expires_on이 없으므로, 현재 시간 + expires_in으로 계산
            token.expires_at = datetime.now().replace(microsecond=0)
        
        return token
    
    def is_expired(self) -> bool:
        """토큰이 만료되었는지 확인합니다.
        
        Returns:
            bool: 만료되었으면 True, 아니면 False
        """
        if not self.expires_at:
            return True
            
        # 만료 시간이 현재 시간보다 이전이면 만료된 것으로 간주
        return self.expires_at < datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """TokenCredential 객체를 딕셔너리로 변환합니다.
        
        Returns:
            Dict[str, Any]: 변환된 딕셔너리
        """
        result = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "ext_expires_in": self.ext_expires_in,
            "scope": self.scope
        }
        
        if self.refresh_token:
            result["refresh_token"] = self.refresh_token
            
        if self.id_token:
            result["id_token"] = self.id_token
            
        if self.expires_at:
            result["expires_on"] = int(self.expires_at.timestamp())
            
        return result


@dataclass
class UserInfo:
    """사용자 정보 클래스
    
    Microsoft Graph API에서 반환한 사용자 정보를 포함하는 데이터 클래스입니다.
    
    Attributes:
        id (str): 사용자 ID
        display_name (str): 표시 이름
        given_name (Optional[str]): 이름
        surname (Optional[str]): 성
        user_principal_name (str): 사용자 계정 이름 (일반적으로 이메일)
        mail (Optional[str]): 이메일
        mail_nickname (Optional[str]): 메일 별명
        job_title (Optional[str]): 직책
        office_location (Optional[str]): 회사 위치
        business_phones (List[str]): 회사 전화번호 목록
        mobile_phone (Optional[str]): 휴대폰 번호
        preferred_language (Optional[str]): 선호 언어
        raw_data (Dict[str, Any]): 원본 데이터
    """
    
    id: str
    display_name: str
    user_principal_name: str
    given_name: Optional[str] = None
    surname: Optional[str] = None
    mail: Optional[str] = None
    mail_nickname: Optional[str] = None
    job_title: Optional[str] = None
    office_location: Optional[str] = None
    business_phones: List[str] = field(default_factory=list)
    mobile_phone: Optional[str] = None
    preferred_language: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInfo':
        """딕셔너리에서 UserInfo 객체를 생성합니다.
        
        Args:
            data (Dict[str, Any]): 사용자 정보가 포함된 딕셔너리
            
        Returns:
            UserInfo: 생성된 UserInfo 객체
        """
        return cls(
            id=data.get("id", ""),
            display_name=data.get("displayName", ""),
            user_principal_name=data.get("userPrincipalName", ""),
            given_name=data.get("givenName"),
            surname=data.get("surname"),
            mail=data.get("mail"),
            mail_nickname=data.get("mailNickname"),
            job_title=data.get("jobTitle"),
            office_location=data.get("officeLocation"),
            business_phones=data.get("businessPhones", []),
            mobile_phone=data.get("mobilePhone"),
            preferred_language=data.get("preferredLanguage"),
            raw_data=data
        )


@dataclass
class AuthStatus:
    """인증 상태 클래스
    
    현재 인증 상태 정보를 포함하는 데이터 클래스입니다.
    
    Attributes:
        is_authenticated (bool): 인증되었는지 여부
        user_info (Optional[UserInfo]): 인증된 사용자 정보 (인증되지 않은 경우 None)
        scopes (List[str]): 허용된 권한 범위
        token_expires_at (Optional[datetime]): 토큰 만료 일시 (인증되지 않은 경우 None)
        auth_method (Optional[str]): 인증 방법 (인증되지 않은 경우 None)
    """
    
    is_authenticated: bool
    scopes: List[str] = field(default_factory=list)
    user_info: Optional[UserInfo] = None
    token_expires_at: Optional[datetime] = None
    auth_method: Optional[str] = None


@dataclass
class AuthResult:
    """인증 결과 클래스
    
    인증 프로세스 결과 정보를 포함하는 데이터 클래스입니다.
    
    Attributes:
        success (bool): 인증 성공 여부
        status (AuthStatus): 인증 상태
        error_message (Optional[str]): 오류 메시지 (인증 실패 시)
        auth_response (Optional[Dict[str, Any]]): 인증 응답 데이터 (디버깅용)
    """
    
    success: bool
    status: AuthStatus
    error_message: Optional[str] = None
    auth_response: Optional[Dict[str, Any]] = None
