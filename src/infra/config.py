"""설정 관리 모듈

이 모듈은 애플리케이션 설정을 관리합니다.
환경 변수에서 설정을 로드하고 기본 설정값을 제공합니다.
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import ConfigurationError


# 로거 설정
logger = LoggerFactory.get_logger(__name__)

# .env 파일 로드
dotenv_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / ".env"
load_dotenv(dotenv_path=dotenv_path)

# 로드 결과 로깅
if os.path.exists(dotenv_path):
    logger.debug(f".env 파일을 로드했습니다: {dotenv_path}")
else:
    logger.warning(f".env 파일을 찾을 수 없습니다: {dotenv_path}")


class Config:
    """애플리케이션 설정 클래스
    
    환경 변수에서 설정을 로드하고 기본 설정값을 제공합니다.
    """
    
    # API 기본 설정
    API_BASE_URL = os.environ.get("API_BASE_URL", "https://graph.microsoft.com")
    API_VERSION = os.environ.get("API_VERSION", "v1.0")
    
    # 인증 설정
    CLIENT_ID = os.environ.get("CLIENT_ID")
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
    TENANT_ID = os.environ.get("TENANT_ID", "common")
    REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:8000")
    
    # REDIRECT_URI에서 포트 추출 (없으면 환경변수 또는 기본값 사용)
    try:
        from urllib.parse import urlparse
        _parsed_uri = urlparse(REDIRECT_URI)
        _extracted_port = _parsed_uri.port
    except:
        _extracted_port = None

    # AUTH_PORT를 설정하는 로직: URI에서 추출한 포트 > 환경변수 > 기본값(5000)
    AUTH_PORT = int(os.environ.get("AUTH_PORT", str(_extracted_port or 5000)))
    DEFAULT_AUTH_METHOD = os.environ.get("DEFAULT_AUTH_METHOD", "interactive")
    
    # 권한 범위
    # (참고: 'openid', 'offline_access', 'profile'는 MSAL에서 자동으로 추가됨)
    _DEFAULT_SCOPES = "Mail.Read,Mail.ReadWrite,Mail.Send,User.Read"
    _SCOPES = os.environ.get("SCOPES", _DEFAULT_SCOPES)
    SCOPES = [scope.strip() for scope in _SCOPES.split(",")]
    
    # 캐시 파일 경로
    TOKEN_CACHE_FILE = os.environ.get(
        "TOKEN_CACHE_FILE", 
        str(Path(os.path.dirname(__file__)) / ".token_cache.json")
    )
    
    DELTA_LINK_FILE = os.environ.get(
        "DELTA_LINK_FILE", 
        str(Path(os.path.dirname(__file__)) / ".delta_link.json")
    )
    
    # 이메일 조회 기본 설정
    DEFAULT_DAYS = int(os.environ.get("DEFAULT_DAYS", "7"))
    DEFAULT_LIMIT = int(os.environ.get("DEFAULT_LIMIT", "50"))
    
    # 필터링 설정
    _FILTER_SENDERS = os.environ.get("FILTER_SENDERS", "block@krs.co.kr,Administrator")
    FILTER_SENDERS = [sender.strip() for sender in _FILTER_SENDERS.split(",") if sender.strip()]
    
    @classmethod
    def validate(cls) -> bool:
        """설정 유효성을 검사합니다.
        
        Returns:
            bool: 설정이 유효하면 True, 그렇지 않으면 False
            
        Raises:
            ConfigurationError: 필수 설정이 누락된 경우
        """
        missing_vars = []
        
        if not cls.CLIENT_ID:
            missing_vars.append("CLIENT_ID")
            
        if not cls.CLIENT_SECRET:
            missing_vars.append("CLIENT_SECRET")
            
        if not cls.TENANT_ID:
            missing_vars.append("TENANT_ID")
            
        if not cls.REDIRECT_URI:
            missing_vars.append("REDIRECT_URI")
            
        if missing_vars:
            error_msg = f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
            
        return True
    
    @classmethod
    def get_api_url(cls) -> str:
        """API 기본 URL을 반환합니다.
        
        Returns:
            str: API 기본 URL
        """
        return f"{cls.API_BASE_URL}/{cls.API_VERSION}"
    
    @classmethod
    def get_filter_senders(cls) -> List[str]:
        """필터링할 발신자 목록을 반환합니다.
        
        Returns:
            List[str]: 필터링할 발신자 목록
        """
        return cls.FILTER_SENDERS
    
    @classmethod
    def add_filter_sender(cls, sender: str) -> None:
        """필터링할 발신자를 추가합니다.
        
        Args:
            sender (str): 추가할 발신자
        """
        if sender and sender not in cls.FILTER_SENDERS:
            cls.FILTER_SENDERS.append(sender)
            logger.debug(f"필터링할 발신자 추가: {sender}")
    
    @classmethod
    def remove_filter_sender(cls, sender: str) -> bool:
        """필터링할 발신자를 제거합니다.
        
        Args:
            sender (str): 제거할 발신자
            
        Returns:
            bool: 제거 성공 여부
        """
        if sender in cls.FILTER_SENDERS:
            cls.FILTER_SENDERS.remove(sender)
            logger.debug(f"필터링할 발신자 제거: {sender}")
            return True
        return False
    
    @classmethod
    def get_delta_link(cls, key: str) -> Optional[str]:
        """델타 링크를 반환합니다.
        
        Args:
            key (str): 델타 링크 키 (예: 'inbox', 'sentItems')
            
        Returns:
            Optional[str]: 델타 링크, 없으면 None
        """
        try:
            if not os.path.exists(cls.DELTA_LINK_FILE):
                return None
                
            with open(cls.DELTA_LINK_FILE, "r") as f:
                delta_links = json.load(f)
                
            return delta_links.get(key)
        except Exception as e:
            logger.error(f"델타 링크 조회 중 오류 발생: {str(e)}")
            return None
    
    @classmethod
    def save_delta_link(cls, key: str, delta_link: str) -> None:
        """델타 링크를 저장합니다.
        
        Args:
            key (str): 델타 링크 키 (예: 'inbox', 'sentItems')
            delta_link (str): 델타 링크
        """
        try:
            delta_links = {}
            
            if os.path.exists(cls.DELTA_LINK_FILE):
                with open(cls.DELTA_LINK_FILE, "r") as f:
                    delta_links = json.load(f)
            
            delta_links[key] = delta_link
            
            # 파일 디렉토리가 없으면 생성
            os.makedirs(os.path.dirname(cls.DELTA_LINK_FILE), exist_ok=True)
            
            with open(cls.DELTA_LINK_FILE, "w") as f:
                json.dump(delta_links, f, indent=2)
                
            logger.debug(f"델타 링크 저장 완료: key={key}")
        except Exception as e:
            logger.error(f"델타 링크 저장 중 오류 발생: {str(e)}")
    
    @classmethod
    def reset_delta_link(cls, key: Optional[str] = None) -> None:
        """델타 링크를 초기화합니다.
        
        Args:
            key (Optional[str], optional): 초기화할 델타 링크 키. 
                지정하지 않으면 모든 키를 초기화합니다.
        """
        try:
            if not os.path.exists(cls.DELTA_LINK_FILE):
                return
                
            if key is None:
                # 모든 델타 링크 초기화
                if os.path.exists(cls.DELTA_LINK_FILE):
                    os.remove(cls.DELTA_LINK_FILE)
                logger.debug("모든 델타 링크 초기화 완료")
            else:
                # 특정 키만 초기화
                with open(cls.DELTA_LINK_FILE, "r") as f:
                    delta_links = json.load(f)
                
                if key in delta_links:
                    del delta_links[key]
                    
                    with open(cls.DELTA_LINK_FILE, "w") as f:
                        json.dump(delta_links, f, indent=2)
                        
                    logger.debug(f"델타 링크 초기화 완료: key={key}")
        except Exception as e:
            logger.error(f"델타 링크 초기화 중 오류 발생: {str(e)}")


# 설정 로드 로깅
logger.debug(f"API 기본 URL: {Config.API_BASE_URL}/{Config.API_VERSION}")
logger.debug(f"테넌트 ID: {Config.TENANT_ID}")
logger.debug(f"리디렉션 URI: {Config.REDIRECT_URI}")
logger.debug(f"권한 범위: {Config.SCOPES}")
logger.debug(f"기본 조회 기간: {Config.DEFAULT_DAYS}일")
logger.debug(f"기본 조회 개수: {Config.DEFAULT_LIMIT}개")
logger.debug(f"필터링할 발신자: {Config.FILTER_SENDERS}")
