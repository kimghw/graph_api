"""인증 토큰 관리 모듈

이 모듈은 Microsoft Graph API 인증 토큰을 관리합니다.
"""

import os
import json
import webbrowser
import socket
import msal
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
import http.server
import threading

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import AuthenticationError, TokenCacheError
from src.infra.config import Config
from src.schemas.auth import TokenCredential, UserInfo, AuthStatus, AuthResult


# 로거 설정
logger = LoggerFactory.get_logger(__name__)


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """콜백 핸들러 클래스
    
    리디렉션 URI로 전달되는 인증 코드를 처리하는 HTTP 핸들러입니다.
    """
    
    # 인증 코드를 저장할 클래스 변수
    auth_code = None
    
    def do_GET(self):
        """GET 요청을 처리합니다."""
        # URL에서 쿼리 매개변수 추출
        query_components = parse_qs(urlparse(self.path).query)
        
        if 'code' in query_components:
            # 인증 코드 저장
            CallbackHandler.auth_code = query_components['code'][0]
            
            # 응답 전송
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Microsoft Graph API 인증 성공</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .container {
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #fff;
                        padding: 20px;
                        border-radius: 5px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #0078d4;
                        margin-top: 0;
                    }
                    .success-icon {
                        color: #107c10;
                        font-size: 48px;
                        margin-bottom: 20px;
                    }
                    .info {
                        background-color: #f0f6ff;
                        padding: 15px;
                        border-left: 4px solid #0078d4;
                        margin-bottom: 20px;
                    }
                    .countdown {
                        font-weight: bold;
                        color: #666;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-icon">✓</div>
                    <h1>인증이 성공적으로 완료되었습니다!</h1>
                    
                    <div class="info">
                        <p><strong>Microsoft Graph API</strong>에 성공적으로 인증되었습니다.</p>
                        <p>Microsoft 계정으로 성공적으로 로그인되었습니다.</p>
                    </div>
                    
                    <p>이 창은 5초 후에 자동으로 닫힙니다. 애플리케이션으로 돌아가서 진행하세요.</p>
                    <p class="countdown">창 닫히는 시간: <span id="timer">5</span>초</p>
                    
                    <script>
                        // 여러 브라우저 호환성을 위한 창 닫기 함수
                        function closeWindow() {
                            // 다양한 창 닫기 메소드 시도
                            window.close();
                            window.open('', '_self').close();
                            window.open('about:blank', '_self').close();
                            
                            // 위 방법이 실패하면 페이지 내용을 지우고 닫기 메시지 표시
                            if (document.body) {
                                document.body.innerHTML = 
                                    "<div style='text-align:center; padding:20px;'>" +
                                    "<h3>인증이 완료되었습니다.</h3>" +
                                    "<p>이 창은 자동으로 닫히지 않았습니다. 창을 직접 닫아주세요.</p>" +
                                    "</div>";
                            }
                        }
                        
                        // 카운트다운 타이머
                        var seconds = 3; // 3초로 단축
                        var timer = setInterval(function() {
                            seconds--;
                            document.getElementById('timer').textContent = seconds;
                            if (seconds <= 0) {
                                clearInterval(timer);
                                closeWindow();
                            }
                        }, 1000);
                        
                        // 페이지 로드 완료 시 자동 닫기 시도
                        window.onload = function() {
                            setTimeout(closeWindow, 3000);
                        };
                    </script>
                </div>
            </body>
            </html>
            """.encode())
        else:
            # 오류 응답 전송
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
            <html>
            <head>
                <meta charset="UTF-8">
                <title>인증 오류</title>
            </head>
            <body>
                <h1>인증 중 오류가 발생했습니다!</h1>
                <p>오류 코드: {}</p>
                <p>오류 설명: {}</p>
            </body>
            </html>
            """.format(
                query_components.get('error', ['알 수 없는 오류'])[0],
                query_components.get('error_description', ['설명 없음'])[0]
            ).encode())
    
    def log_message(self, format, *args):
        """로깅을 무시합니다."""
        # HTTP 서버의 로그를 표시하지 않음
        pass


class AuthTokenManager:
    """인증 토큰 관리자 클래스
    
    Microsoft Graph API 인증 프로세스를 처리하고 토큰을 관리합니다.
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        """초기화 메소드
        
        Args:
            tenant_id (Optional[str], optional): 테넌트 ID. 
                지정하지 않으면 Config.TENANT_ID 사용.
        """
        # 환경 변수 또는 config에서 값 로드
        self.tenant_id = tenant_id or Config.TENANT_ID
        self.client_id = Config.CLIENT_ID
        self.client_secret = Config.CLIENT_SECRET
        self.redirect_uri = Config.REDIRECT_URI
        self.scopes = Config.SCOPES
        self.token_cache_file = Config.TOKEN_CACHE_FILE
        
        # 토큰 캐시 객체 생성
        self.token_cache = msal.SerializableTokenCache()
        self._load_cache()
        
        # MSAL 애플리케이션 객체 생성
        # 명시적으로 테넌트 ID 지정
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            token_cache=self.token_cache
        )
        
        logger.debug(f"AuthTokenManager 초기화 완료 (테넌트 ID: {self.tenant_id})")
    
    def get_auth_url(self) -> str:
        """인증 URL을 생성합니다.
        
        Returns:
            str: 인증 URL
        """
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state="state123",  # 보안을 위해 랜덤 값을 사용하는 것이 좋음
            prompt="select_account"  # 계정 선택 프롬프트 표시
        )
        logger.debug(f"인증 URL 생성: {auth_url}")
        return auth_url
    
    def get_token(self) -> Optional[Dict[str, Any]]:
        """액세스 토큰을 조회합니다. 없거나 만료된 경우 갱신을 시도합니다.
        
        Returns:
            Optional[Dict[str, Any]]: 토큰 정보가 포함된 딕셔너리, 획득 실패 시 None
        """
        accounts = self.app.get_accounts()
        
        if not accounts:
            logger.warning("계정 정보 없음")
            return None
        
        # 첫 번째 계정에 대해 토큰 획득 시도
        result = self._get_token_silent(accounts[0])
        
        if not result:
            logger.warning("액세스 토큰 조회 실패")
            return None
            
        logger.debug("액세스 토큰 조회 성공")
        return result
    
    def get_token_from_code(self, auth_code: str) -> Dict[str, Any]:
        """인증 코드로 토큰을 획득합니다.
        
        Args:
            auth_code (str): 인증 코드
            
        Returns:
            Dict[str, Any]: 토큰 정보가 포함된 딕셔너리
            
        Raises:
            AuthenticationError: 토큰 획득 실패 시
        """
        try:
            result = self.app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "error" in result:
                error_msg = f"인증 코드로 토큰 획득 실패: {result.get('error')}"
                logger.error(f"{error_msg} - {result.get('error_description')}")
                raise AuthenticationError(
                    error_msg,
                    auth_error_type=result.get("error"),
                    error_description=result.get("error_description")
                )
            
            # 토큰 캐시 저장
            self._save_cache()
            
            logger.debug("인증 코드로 토큰 획득 성공")
            return result
        except Exception as e:
            if not isinstance(e, AuthenticationError):
                logger.exception("인증 코드로 토큰 획득 중 예외 발생")
                raise AuthenticationError(f"인증 코드로 토큰 획득 중 예외 발생: {str(e)}")
            raise
    
    def authenticate_code_flow(self) -> AuthResult:
        """인증 코드 흐름으로 인증합니다.
        
        Returns:
            AuthResult: 인증 결과
        """
        try:
            # 리디렉션 URI의 포트 추출
            parsed_uri = urlparse(self.redirect_uri)
            port = parsed_uri.port or Config.AUTH_PORT  # 설정에서 포트 가져오기
            logger.debug(f"인증 콜백 서버에 포트 {port} 사용")
            
            # 인증 코드를 수신할 로컬 서버 시작
            server = http.server.HTTPServer(('127.0.0.1', port), CallbackHandler)
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            logger.debug(f"로컬 서버 시작됨 (포트: {port})")
            
            # 인증 URL 생성 및 브라우저 열기
            auth_url = self.get_auth_url()
            webbrowser.open(auth_url)
            
            logger.debug("브라우저에서 인증 진행 중...")
            
            # 인증 코드 수신 대기 (최대 5분)
            timeout = datetime.now() + timedelta(minutes=5)
            while not CallbackHandler.auth_code and datetime.now() < timeout:
                pass
            
            # 서버 종료
            server.shutdown()
            server.server_close()
            
            if not CallbackHandler.auth_code:
                error_msg = "인증 코드 수신 시간 초과"
                logger.error(error_msg)
                return AuthResult(
                    success=False,
                    status=AuthStatus(is_authenticated=False),
                    error_message=error_msg
                )
            
            # 인증 코드로 토큰 획득
            auth_code = CallbackHandler.auth_code
            CallbackHandler.auth_code = None  # 코드 초기화
            
            token_response = self.get_token_from_code(auth_code)
            
            # 사용자 정보 조회
            user_info = self._get_user_info(token_response.get("access_token"))
            
            # 토큰 만료 시간 계산
            expires_at = datetime.now() + timedelta(seconds=token_response.get("expires_in", 0))
            
            # 인증 결과 반환
            return AuthResult(
                success=True,
                status=AuthStatus(
                    is_authenticated=True,
                    user_info=user_info,
                    scopes=token_response.get("scope", "").split(),
                    token_expires_at=expires_at,
                    auth_method="authorization_code"
                )
            )
        except AuthenticationError as e:
            logger.error(f"인증 코드 흐름 인증 실패: {str(e)}")
            return AuthResult(
                success=False,
                status=AuthStatus(is_authenticated=False),
                error_message=str(e)
            )
        except Exception as e:
            logger.exception("인증 코드 흐름 인증 중 예외 발생")
            return AuthResult(
                success=False,
                status=AuthStatus(is_authenticated=False),
                error_message=f"인증 중 예외 발생: {str(e)}"
            )
    
    def authenticate_device_flow(self) -> AuthResult:
        """디바이스 코드 흐름으로, 인증합니다.
        
        Returns:
            AuthResult: 인증 결과
        """
        try:
            # 디바이스 코드 흐름 시작
            flow = self.app.initiate_device_flow(scopes=self.scopes)
            
            if "error" in flow:
                error_msg = f"디바이스 코드 흐름 시작 실패: {flow.get('error')}"
                logger.error(f"{error_msg} - {flow.get('error_description')}")
                return AuthResult(
                    success=False,
                    status=AuthStatus(is_authenticated=False),
                    error_message=error_msg
                )
            
            # 사용자에게 지침 출력
            print(flow["message"])
            
            # 토큰 획득
            token_response = self.app.acquire_token_by_device_flow(flow)
            
            if "error" in token_response:
                error_msg = f"디바이스 코드 흐름 토큰 획득 실패: {token_response.get('error')}"
                logger.error(f"{error_msg} - {token_response.get('error_description')}")
                return AuthResult(
                    success=False,
                    status=AuthStatus(is_authenticated=False),
                    error_message=error_msg
                )
            
            # 토큰 캐시 저장
            self._save_cache()
            
            # 사용자 정보 조회
            user_info = self._get_user_info(token_response.get("access_token"))
            
            # 토큰 만료 시간 계산
            expires_at = datetime.now() + timedelta(seconds=token_response.get("expires_in", 0))
            
            # 인증 결과 반환
            return AuthResult(
                success=True,
                status=AuthStatus(
                    is_authenticated=True,
                    user_info=user_info,
                    scopes=token_response.get("scope", "").split(),
                    token_expires_at=expires_at,
                    auth_method="device_flow"
                )
            )
        except Exception as e:
            logger.exception("디바이스 코드 흐름 인증 중 예외 발생")
            return AuthResult(
                success=False,
                status=AuthStatus(is_authenticated=False),
                error_message=f"인증 중 예외 발생: {str(e)}"
            )
    
    def authenticate_client_credentials(self) -> AuthResult:
        """클라이언트 자격 증명 흐름으로 인증합니다.
        
        Returns:
            AuthResult: 인증 결과
        """
        try:
            # 클라이언트 자격 증명 흐름으로 토큰 획득
            # 클라이언트 자격 증명 흐름에서는 /.default 접미사가 필요
            default_scopes = ["https://graph.microsoft.com/.default"]
            token_response = self.app.acquire_token_for_client(scopes=default_scopes)
            
            if "error" in token_response:
                error_msg = f"클라이언트 자격 증명 흐름 토큰 획득 실패: {token_response.get('error')}"
                logger.error(f"{error_msg} - {token_response.get('error_description')}")
                return AuthResult(
                    success=False,
                    status=AuthStatus(is_authenticated=False),
                    error_message=error_msg
                )
            
            # 토큰 캐시 저장
            self._save_cache()
            
            # 토큰 만료 시간 계산
            expires_at = datetime.now() + timedelta(seconds=token_response.get("expires_in", 0))
            
            # 인증 결과 반환 (사용자 정보 없음)
            return AuthResult(
                success=True,
                status=AuthStatus(
                    is_authenticated=True,
                    user_info=None,  # 클라이언트 자격 증명 흐름에서는 사용자 정보 없음
                    scopes=token_response.get("scope", "").split(),
                    token_expires_at=expires_at,
                    auth_method="client_credentials"
                )
            )
        except Exception as e:
            logger.exception("클라이언트 자격 증명 흐름 인증 중 예외 발생")
            return AuthResult(
                success=False,
                status=AuthStatus(is_authenticated=False),
                error_message=f"인증 중 예외 발생: {str(e)}"
            )
    
    def is_authenticated(self) -> bool:
        """현재 인증 상태를 확인합니다.
        
        Returns:
            bool: 인증되었으면 True, 아니면 False
        """
        # 이 메소드는 계정 정보를 체크하지만, 클라이언트 자격 증명 흐름과 호환성을 위해 수정
        try:
            # 1. 먼저 계정 기반으로 체크 (사용자 인증 흐름)
            accounts = self.app.get_accounts()
            if accounts:
                return True
            
            # 2. 계정이 없는 경우, 클라이언트 자격 증명 흐름의 토큰 체크
            # 클라이언트 자격 증명 흐름에서는 /.default 접미사가 필요
            default_scopes = ["https://graph.microsoft.com/.default"]
            token = self.app.acquire_token_for_client(scopes=default_scopes)
            
            # access_token이 있다면 인증된 것으로 판단
            if token and "access_token" in token and "error" not in token:
                return True
                
            return False
        except Exception as e:
            logger.error(f"인증 상태 확인 중 오류 발생: {str(e)}")
            return False
    
    def get_auth_status(self) -> AuthStatus:
        """현재 인증 상태 정보를 반환합니다.
        
        Returns:
            AuthStatus: 인증 상태 정보
        """
        token = self.get_token()
        
        if not token:
            return AuthStatus(is_authenticated=False)
        
        # 사용자 정보 조회
        user_info = self._get_user_info(token.get("access_token"))
        
        # 토큰 만료 시간 계산
        expires_at = datetime.now() + timedelta(seconds=token.get("expires_in", 0))
        
        # 인증 방법 확인
        auth_method = "unknown"
        if "scope" in token and ".default" in token["scope"]:
            auth_method = "client_credentials"
        elif self.app.get_accounts():
            auth_method = "user_flow"  # 인증 코드 또는 디바이스 코드 흐름
        
        # 권한 범위 확인
        scopes = token.get("scope", "").split()
        
        return AuthStatus(
            is_authenticated=True,
            user_info=user_info,
            scopes=scopes,
            token_expires_at=expires_at,
            auth_method=auth_method
        )
    
    def get_user_info(self) -> Optional[UserInfo]:
        """현재 인증된 사용자 정보를 반환합니다.
        
        Returns:
            Optional[UserInfo]: 사용자 정보, 인증되지 않았거나 오류 발생 시 None
        """
        token = self.get_token()
        
        if not token:
            return None
            
        return self._get_user_info(token.get("access_token"))
    
    def logout(self) -> bool:
        """로그아웃합니다.
        
        Returns:
            bool: 로그아웃 성공 여부
        """
        try:
            # 모든 계정 제거
            accounts = self.app.get_accounts()
            for account in accounts:
                self.app.remove_account(account)
            
            # 토큰 캐시 초기화
            self.token_cache = msal.SerializableTokenCache()
            self.app._token_cache = self.token_cache
            
            # 캐시 파일 제거
            if os.path.exists(self.token_cache_file):
                os.remove(self.token_cache_file)
                
            logger.debug("로그아웃 완료")
            return True
        except Exception as e:
            logger.exception("로그아웃 중 예외 발생")
            return False
    
    def _get_token_silent(self, account) -> Optional[Dict[str, Any]]:
        """토큰을 조용히 획득합니다. (갱신 시도)
        
        Args:
            account: 계정 객체
            
        Returns:
            Optional[Dict[str, Any]]: 토큰 정보가 포함된 딕셔너리, 획득 실패 시 None
        """
        result = self.app.acquire_token_silent(
            scopes=self.scopes,
            account=account
        )
        
        if not result:
            logger.debug("토큰 갱신 필요")
            return None
            
        logger.debug("토큰 조용히 획득 성공")
        return result
    
    def _get_user_info(self, access_token: str) -> Optional[UserInfo]:
        """액세스 토큰으로 사용자 정보를 조회합니다.
        
        Args:
            access_token (str): 액세스 토큰
            
        Returns:
            Optional[UserInfo]: 사용자 정보, 오류 발생 시 None
        """
        import requests
        
        # Microsoft Graph API에 사용자 정보 요청
        graph_url = f"{Config.get_api_url()}/me"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            return UserInfo.from_dict(user_data)
        except Exception as e:
            logger.exception("사용자 정보 조회 중 예외 발생")
            return None
    
    def _save_cache(self) -> None:
        """토큰 캐시를 파일에 저장합니다."""
        try:
            # 직렬화된 캐시 데이터 확인
            cache_data = self.token_cache.serialize()
            
            # 캐시 데이터가 비어있지 않은 경우에만 저장
            if cache_data and len(cache_data) > 2:  # "{}" 이상의 내용이 있는지 확인
                # 토큰 캐시 파일 경로가 비어있는 경우 기본 경로 사용
                if not self.token_cache_file:
                    self.token_cache_file = os.path.join(os.path.dirname(__file__), ".token_cache.json")
                    logger.warning(f"토큰 캐시 파일 경로가 비어 있어 기본 경로로 설정합니다: {self.token_cache_file}")
                
                # 경로 객체 생성
                cache_file_path = Path(self.token_cache_file)
                
                # 디렉토리 경로 확인 및 생성
                cache_dir = cache_file_path.parent
                if str(cache_dir) and str(cache_dir) != '.':
                    os.makedirs(cache_dir, exist_ok=True)
                
                # 파일에 캐시 데이터 저장
                with open(self.token_cache_file, 'w') as cache_file:
                    cache_file.write(cache_data)
                    
                logger.debug(f"토큰 캐시 저장 완료: {self.token_cache_file}")
        except Exception as e:
            logger.exception("토큰 캐시 저장 중 예외 발생")
            raise TokenCacheError(f"토큰 캐시 저장 중 오류 발생: {str(e)}")
    
    def _load_cache(self) -> None:
        """파일에서 토큰 캐시를 로드합니다."""
        try:
            if os.path.exists(self.token_cache_file):
                with open(self.token_cache_file, 'r') as cache_file:
                    self.token_cache.deserialize(cache_file.read())
                    
                logger.debug(f"토큰 캐시 로드 완료: {self.token_cache_file}")
        except Exception as e:
            logger.exception("토큰 캐시 로드 중 예외 발생")
            raise TokenCacheError(f"토큰 캐시 로드 중 오류 발생: {str(e)}")
