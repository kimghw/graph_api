"""인증 서비스 모듈

이 모듈은 인증 관련 비즈니스 로직을 제공합니다.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import AuthenticationError
from src.infra.auth_token import AuthTokenManager
from src.schemas.auth import TokenCredential, UserInfo, AuthStatus, AuthResult


# 로거 설정
logger = LoggerFactory.get_logger(__name__)


class AuthService:
    """인증 서비스 클래스
    
    인증 관련 비즈니스 로직을 제공합니다.
    """
    
    def __init__(self):
        """초기화 메소드"""
        self.auth_manager = AuthTokenManager()
        logger.debug("AuthService 초기화 완료")
    
    def authenticate_interactive(self) -> AuthResult:
        """대화형 인증을 수행합니다.
        
        브라우저를 열어 사용자가 Microsoft 계정으로 로그인하는 방식의 인증입니다.
        
        Returns:
            AuthResult: 인증 결과
        """
        logger.info("대화형 인증 시작")
        
        # 이미 인증된 경우 토큰이 유효한지 확인
        if self.auth_manager.is_authenticated():
            logger.debug("이미 인증된 상태, 토큰 유효성 확인")
            status = self.auth_manager.get_auth_status()
            
            # 토큰이 30분 이상 남았으면 재인증 필요 없음
            if status.token_expires_at and status.token_expires_at > (datetime.now() + timedelta(minutes=30)):
                logger.info("유효한 토큰 존재, 재인증 불필요")
                return AuthResult(
                    success=True,
                    status=status
                )
                
            logger.debug("토큰 만료 예정, 재인증 필요")
        
        # 인증 코드 흐름으로 인증
        auth_result = self.auth_manager.authenticate_code_flow()
        
        if auth_result.success:
            logger.info("대화형 인증 성공")
        else:
            logger.error(f"대화형 인증 실패: {auth_result.error_message}")
            
        return auth_result
    
    def authenticate_device(self) -> AuthResult:
        """디바이스 코드 인증을 수행합니다.
        
        다른 장치에서 코드를 입력하여 인증하는 방식입니다.
        
        Returns:
            AuthResult: 인증 결과
        """
        logger.info("디바이스 코드 인증 시작")
        
        # 이미 인증된 경우 토큰이 유효한지 확인
        if self.auth_manager.is_authenticated():
            logger.debug("이미 인증된 상태, 토큰 유효성 확인")
            status = self.auth_manager.get_auth_status()
            
            # 토큰이 30분 이상 남았으면 재인증 필요 없음
            if status.token_expires_at and status.token_expires_at > (datetime.now() + timedelta(minutes=30)):
                logger.info("유효한 토큰 존재, 재인증 불필요")
                return AuthResult(
                    success=True,
                    status=status
                )
                
            logger.debug("토큰 만료 예정, 재인증 필요")
        
        # 디바이스 코드 흐름으로 인증
        auth_result = self.auth_manager.authenticate_device_flow()
        
        if auth_result.success:
            logger.info("디바이스 코드 인증 성공")
        else:
            logger.error(f"디바이스 코드 인증 실패: {auth_result.error_message}")
            
        return auth_result
    
    def authenticate_client_credentials(self) -> AuthResult:
        """클라이언트 자격 증명 인증을 수행합니다.
        
        사용자 상호 작용 없이 애플리케이션 자격 증명으로 인증하는 방식입니다.
        
        Returns:
            AuthResult: 인증 결과
        """
        logger.info("클라이언트 자격 증명 인증 시작")
        
        # 이미 인증된 경우 토큰이 유효한지 확인
        if self.auth_manager.is_authenticated():
            logger.debug("이미 인증된 상태, 토큰 유효성 확인")
            status = self.auth_manager.get_auth_status()
            
            # 토큰이 30분 이상 남았으면 재인증 필요 없음
            if status.token_expires_at and status.token_expires_at > (datetime.now() + timedelta(minutes=30)):
                logger.info("유효한 토큰 존재, 재인증 불필요")
                return AuthResult(
                    success=True,
                    status=status
                )
                
            logger.debug("토큰 만료 예정, 재인증 필요")
        
        # 클라이언트 자격 증명 흐름으로 인증
        auth_result = self.auth_manager.authenticate_client_credentials()
        
        if auth_result.success:
            logger.info("클라이언트 자격 증명 인증 성공")
        else:
            logger.error(f"클라이언트 자격 증명 인증 실패: {auth_result.error_message}")
            
        return auth_result
    
    def get_token(self) -> Optional[Dict[str, Any]]:
        """현재 액세스 토큰을 조회합니다.
        
        Returns:
            Optional[Dict[str, Any]]: 토큰 정보가 포함된 딕셔너리, 인증되지 않은 경우 None
        """
        return self.auth_manager.get_token()
    
    def get_auth_status(self) -> AuthStatus:
        """현재 인증 상태를 조회합니다.
        
        Returns:
            AuthStatus: 인증 상태 정보
        """
        return self.auth_manager.get_auth_status()
    
    def get_user_info(self) -> Optional[UserInfo]:
        """현재 인증된 사용자 정보를 조회합니다.
        
        Returns:
            Optional[UserInfo]: 사용자 정보, 인증되지 않은 경우 None
        """
        return self.auth_manager.get_user_info()
    
    def logout(self) -> bool:
        """로그아웃합니다.
        
        Returns:
            bool: 로그아웃 성공 여부
        """
        logger.info("로그아웃 시작")
        result = self.auth_manager.logout()
        
        if result:
            logger.info("로그아웃 성공")
        else:
            logger.error("로그아웃 실패")
            
        return result
    
    def is_authenticated(self) -> bool:
        """현재 인증 상태를 확인합니다.
        
        Returns:
            bool: 인증되었으면 True, 아니면 False
        """
        return self.auth_manager.is_authenticated()
    
    def print_auth_status(self) -> None:
        """현재 인증 상태를 출력합니다."""
        status = self.get_auth_status()
        
        if not status.is_authenticated:
            print("인증 상태: 인증되지 않음")
            return
            
        print(f"인증 상태: 인증됨")
        print(f"인증 방법: {status.auth_method}")
        
        if status.token_expires_at:
            expires_in = status.token_expires_at - datetime.now()
            print(f"토큰 만료 시간: {status.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')} (남은 시간: {expires_in})")
            
        if status.user_info:
            print(f"사용자 이름: {status.user_info.display_name}")
            print(f"사용자 이메일: {status.user_info.mail or status.user_info.user_principal_name}")
            
        print(f"권한 범위: {', '.join(status.scopes)}")
