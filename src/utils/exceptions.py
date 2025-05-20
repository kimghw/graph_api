"""예외 처리 모듈

이 모듈은 애플리케이션에서 사용되는 사용자 정의 예외 클래스를 제공합니다.
"""


class BaseError(Exception):
    """애플리케이션 기본 예외 클래스

    모든 사용자 정의 예외의 기본 클래스입니다.
    
    Attributes:
        message (str): 오류 메시지
        details (dict, optional): 추가 오류 상세 정보
    """

    def __init__(self, message, details=None):
        """초기화 메소드
        
        Args:
            message (str): 오류 메시지
            details (dict, optional): 추가 오류 상세 정보. 기본값은 None.
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        """문자열 표현 메소드
        
        Returns:
            str: 예외 메시지 문자열
        """
        if not self.details:
            return self.message
            
        details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
        return f"{self.message} ({details_str})"


class ConfigurationError(BaseError):
    """설정 오류 예외

    설정 관련 오류가 발생했을 때 발생하는 예외입니다.
    """
    pass


class TokenCacheError(BaseError):
    """토큰 캐시 오류 예외

    토큰 캐시 파일 읽기/쓰기 중 오류가 발생했을 때 발생하는 예외입니다.
    """
    pass


class DeltaLinkError(BaseError):
    """델타 링크 오류 예외

    델타 링크 파일 읽기/쓰기 중 오류가 발생했을 때 발생하는 예외입니다.
    """
    pass


class AuthenticationError(BaseError):
    """인증 오류 예외

    인증 과정에서 오류가 발생했을 때 발생하는 예외입니다.
    
    Attributes:
        auth_error_type (str): 인증 오류 유형
        error_description (str): 오류 설명
    """

    def __init__(self, message, auth_error_type=None, error_description=None, details=None):
        """초기화 메소드
        
        Args:
            message (str): 오류 메시지
            auth_error_type (str, optional): 인증 오류 유형. 기본값은 None.
            error_description (str, optional): 오류 설명. 기본값은 None.
            details (dict, optional): 추가 오류 상세 정보. 기본값은 None.
        """
        super_details = details or {}
        
        if auth_error_type:
            super_details["auth_error_type"] = auth_error_type
            
        if error_description:
            super_details["error_description"] = error_description
            
        super().__init__(message, super_details)
        
        self.auth_error_type = auth_error_type
        self.error_description = error_description


class GraphApiError(BaseError):
    """Graph API 오류 예외

    Microsoft Graph API 요청 중 오류가 발생했을 때 발생하는 예외입니다.
    
    Attributes:
        status_code (int): HTTP 상태 코드
        error_code (str): Graph API 오류 코드
        request_id (str): 요청 ID
    """

    def __init__(self, message, status_code=None, error_code=None, request_id=None, details=None):
        """초기화 메소드
        
        Args:
            message (str): 오류 메시지
            status_code (int, optional): HTTP 상태 코드. 기본값은 None.
            error_code (str, optional): Graph API 오류 코드. 기본값은 None.
            request_id (str, optional): 요청 ID. 기본값은 None.
            details (dict, optional): 추가 오류 상세 정보. 기본값은 None.
        """
        super_details = details or {}
        
        if status_code:
            super_details["status_code"] = status_code
            
        if error_code:
            super_details["error_code"] = error_code
            
        if request_id:
            super_details["request_id"] = request_id
            
        super().__init__(message, super_details)
        
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id


class EmailProcessingError(BaseError):
    """이메일 처리 오류 예외

    이메일 처리 중 오류가 발생했을 때 발생하는 예외입니다.
    """
    pass


class CommandError(BaseError):
    """명령 오류 예외

    CLI 명령 처리 중 오류가 발생했을 때 발생하는 예외입니다.
    """
    pass
