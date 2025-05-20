"""CLI 메인 모듈

이 모듈은 CLI 진입점 역할을 합니다.
"""

import click
import sys

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import BaseError
from src.cli.graphapi_cli import graphapi
from src.cli.email_cli import email


# 로거 설정
logger = LoggerFactory.get_logger(__name__)


@click.group()
def cli():
    """Microsoft Graph API를 활용한 이메일 관리 도구"""
    pass


# 하위 명령어 그룹 등록
cli.add_command(graphapi)
cli.add_command(email)


@cli.command()
def version():
    """버전 정보를 출력합니다."""
    from importlib.metadata import version as get_version
    
    try:
        # 패키지 이름이 "graph_api"라고 가정
        # 패키지가 설치되어 있지 않은 경우 오류 처리
        try:
            version = get_version("graph_api")
        except:
            version = "0.1.0"  # 기본 버전
            
        click.echo(f"Microsoft Graph API 이메일 관리 도구 v{version}")
        click.echo("Copyright 2025 All rights reserved.")
    except Exception as e:
        logger.exception("버전 정보 출력 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        cli()
    except BaseError as e:
        logger.exception("명령 실행 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("명령 실행 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)
