"""Graph API CLI 모듈

이 모듈은 Graph API 관련 명령어를 처리합니다.
"""

import click
import sys
from typing import Optional

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import BaseError, AuthenticationError, GraphApiError
from src.services.auth_service import AuthService
from src.infra.config import Config


# 로거 설정
logger = LoggerFactory.get_logger(__name__)


@click.group()
def graphapi():
    """Microsoft Graph API 관련 명령어"""
    pass


@graphapi.command()
@click.option(
    "--method", "-m",
    type=click.Choice(["interactive", "device", "client"]),
    default=Config.DEFAULT_AUTH_METHOD,
    help="인증 방법 (interactive: 브라우저 인증, device: 디바이스 코드 인증, client: 클라이언트 자격 증명 인증)"
)
def auth(method: str):
    """Microsoft Graph API에 인증합니다."""
    try:
        auth_service = AuthService()
        
        # 이미 인증된 경우 확인
        if auth_service.is_authenticated():
            status = auth_service.get_auth_status()
            if status.user_info:
                click.echo(f"이미 인증되어 있습니다. ({status.user_info.display_name})")
                click.echo("다시 인증하려면 먼저 'logout' 명령어로 로그아웃하세요.")
                return
        
        # 선택한 방법으로 인증
        if method == "interactive":
            click.echo("브라우저를 통한 인증을 시작합니다...")
            result = auth_service.authenticate_interactive()
        elif method == "device":
            click.echo("디바이스 코드 인증을 시작합니다...")
            result = auth_service.authenticate_device()
        elif method == "client":
            click.echo("클라이언트 자격 증명 인증을 시작합니다...")
            result = auth_service.authenticate_client_credentials()
        else:
            click.echo(f"지원하지 않는 인증 방법: {method}")
            return
        
        # 인증 결과 처리
        if result.success:
            if result.status.user_info:
                click.echo(f"인증 성공! 사용자: {result.status.user_info.display_name}")
            else:
                click.echo("인증 성공! (사용자 정보 없음)")
        else:
            click.echo(f"인증 실패: {result.error_message}")
            sys.exit(1)
            
    except BaseError as e:
        logger.exception("인증 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("인증 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@graphapi.command()
def status():
    """현재 인증 상태를 확인합니다."""
    try:
        auth_service = AuthService()
        auth_service.print_auth_status()
            
    except BaseError as e:
        logger.exception("인증 상태 확인 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("인증 상태 확인 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@graphapi.command()
def logout():
    """로그아웃합니다."""
    try:
        auth_service = AuthService()
        
        if not auth_service.is_authenticated():
            click.echo("이미 로그아웃 상태입니다.")
            return
            
        result = auth_service.logout()
        
        if result:
            click.echo("로그아웃 성공!")
        else:
            click.echo("로그아웃 실패.")
            sys.exit(1)
            
    except BaseError as e:
        logger.exception("로그아웃 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("로그아웃 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@graphapi.command()
@click.option(
    "--output", "-o",
    help="토큰을 저장할 파일 경로",
    required=False
)
def token(output: Optional[str]):
    """현재 액세스 토큰을 출력합니다."""
    try:
        import json
        
        auth_service = AuthService()
        token_info = auth_service.get_token()
        
        if not token_info:
            click.echo("인증되지 않았습니다. 먼저 'auth' 명령어로 인증하세요.")
            sys.exit(1)
            
        # 출력 또는 파일 저장
        if output:
            with open(output, "w") as f:
                json.dump(token_info, f, indent=2)
            click.echo(f"토큰이 {output} 파일에 저장되었습니다.")
        else:
            token_str = json.dumps(token_info, indent=2)
            click.echo("액세스 토큰:")
            click.echo(token_str)
            
    except BaseError as e:
        logger.exception("토큰 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("토큰 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@graphapi.command()
def whoami():
    """현재 인증된 사용자 정보를 출력합니다."""
    try:
        auth_service = AuthService()
        user_info = auth_service.get_user_info()
        
        if not user_info:
            click.echo("인증되지 않았거나 사용자 정보를 조회할 수 없습니다.")
            click.echo("먼저 'auth' 명령어로 인증하세요.")
            sys.exit(1)
            
        click.echo(f"사용자 ID: {user_info.id}")
        click.echo(f"표시 이름: {user_info.display_name}")
        click.echo(f"메일: {user_info.mail or '(없음)'}")
        click.echo(f"사용자 계정 이름: {user_info.user_principal_name}")
        
        if user_info.job_title:
            click.echo(f"직책: {user_info.job_title}")
            
        if user_info.office_location:
            click.echo(f"사무실 위치: {user_info.office_location}")
            
        if user_info.business_phones:
            click.echo(f"회사 전화번호: {', '.join(user_info.business_phones)}")
            
        if user_info.mobile_phone:
            click.echo(f"휴대폰 번호: {user_info.mobile_phone}")
            
    except BaseError as e:
        logger.exception("사용자 정보 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("사용자 정보 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    graphapi()
