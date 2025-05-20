"""이메일 CLI 모듈

이 모듈은 이메일 관련 명령어를 처리합니다.
"""

import click
import sys
import json
from typing import Optional, List
from datetime import datetime

from rich.console import Console
from rich.table import Table

from src.utils.logging_config import LoggerFactory
from src.utils.exceptions import BaseError, GraphApiError, EmailProcessingError
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.schemas.email import EmailProcessingOptions


# 로거 설정
logger = LoggerFactory.get_logger(__name__)

# Rich 콘솔 생성
console = Console()


@click.group()
def email():
    """이메일 관련 명령어"""
    pass


def _check_auth():
    """인증 상태를 확인합니다."""
    auth_service = AuthService()
    if not auth_service.is_authenticated():
        click.echo("인증되지 않았습니다. 먼저 'graphapi auth' 명령어로 인증하세요.")
        sys.exit(1)


def _format_email_table(emails, show_body=False, max_width=100):
    """이메일 목록을 테이블로 포맷팅합니다."""
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID", style="dim", width=12, no_wrap=True)
    table.add_column("발신자", width=20)
    table.add_column("제목", width=30)
    table.add_column("날짜", width=20)
    
    if show_body:
        table.add_column("본문", width=max_width - 82)
    
    for email in emails:
        row = [
            email.id[:10] + "...",
            f"{email.sender.name} <{email.sender.email}>" if email.sender.name else email.sender.email,
            email.subject,
            (email.received_date or email.sent_date).strftime("%Y-%m-%d %H:%M") if (email.received_date or email.sent_date) else ""
        ]
        
        if show_body:
            # 본문 내용 일부 표시
            body_preview = email.body_content[:200].replace("\n", " ")
            if len(email.body_content) > 200:
                body_preview += "..."
            row.append(body_preview)
            
        table.add_row(*row)
    
    return table


@email.command()
@click.option("--days", "-d", default=7, help="조회할 일수 (기본값: 7일)")
@click.option("--limit", "-l", default=50, help="최대 결과 수 (기본값: 50개)")
@click.option("--show-body/--no-body", default=False, help="본문 미리보기 표시 여부")
@click.option("--output", "-o", help="결과를 저장할 JSON 파일 경로")
def inbox(days, limit, show_body, output):
    """수신함 이메일을 조회합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 이메일 조회
        emails = email_service.get_inbox_emails(days=days, limit=limit)
        
        # 결과 표시
        if output:
            # JSON 파일로 저장
            result = []
            for email in emails:
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": f"{email.sender.name} <{email.sender.email}>",
                    "date": (email.received_date or email.sent_date).isoformat() if (email.received_date or email.sent_date) else None,
                    "is_read": email.is_read
                }
                result.append(email_dict)
                
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            click.echo(f"{len(emails)}개의 이메일이 {output} 파일에 저장되었습니다.")
        else:
            # 콘솔에 테이블로 표시
            console.print(f"최근 {days}일간 수신함 이메일 ({len(emails)}개):")
            
            if not emails:
                console.print("이메일이 없습니다.")
            else:
                table = _format_email_table(emails, show_body)
                console.print(table)
                
    except BaseError as e:
        logger.exception("수신함 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("수신함 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.command()
@click.option("--days", "-d", default=7, help="조회할 일수 (기본값: 7일)")
@click.option("--limit", "-l", default=50, help="최대 결과 수 (기본값: 50개)")
@click.option("--show-body/--no-body", default=False, help="본문 미리보기 표시 여부")
@click.option("--output", "-o", help="결과를 저장할 JSON 파일 경로")
def sent(days, limit, show_body, output):
    """송신함 이메일을 조회합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 이메일 조회
        emails = email_service.get_sent_emails(days=days, limit=limit)
        
        # 결과 표시
        if output:
            # JSON 파일로 저장
            result = []
            for email in emails:
                recipients = [f"{r.name} <{r.email}>" for r in email.recipients]
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "recipients": recipients,
                    "date": (email.sent_date or email.received_date).isoformat() if (email.sent_date or email.received_date) else None
                }
                result.append(email_dict)
                
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            click.echo(f"{len(emails)}개의 이메일이 {output} 파일에 저장되었습니다.")
        else:
            # 콘솔에 테이블로 표시
            console.print(f"최근 {days}일간 송신함 이메일 ({len(emails)}개):")
            
            if not emails:
                console.print("이메일이 없습니다.")
            else:
                table = _format_email_table(emails, show_body)
                console.print(table)
                
    except BaseError as e:
        logger.exception("송신함 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("송신함 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.command()
@click.option("--folder", "-f", default="inbox", type=click.Choice(["inbox", "sentItems"]), help="폴더 (inbox 또는 sentItems)")
@click.option("--show-body/--no-body", default=False, help="본문 미리보기 표시 여부")
@click.option("--output", "-o", help="결과를 저장할 JSON 파일 경로")
def delta(folder, show_body, output):
    """델타 쿼리로 최근 변경된 이메일을 조회합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 델타 쿼리 조회
        emails = email_service.get_delta_emails(folder=folder)
        
        # 결과 표시
        if output:
            # JSON 파일로 저장
            result = []
            for email in emails:
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": f"{email.sender.name} <{email.sender.email}>",
                    "date": (email.received_date or email.sent_date).isoformat() if (email.received_date or email.sent_date) else None,
                    "is_read": email.is_read
                }
                result.append(email_dict)
                
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            click.echo(f"{len(emails)}개의 이메일이 {output} 파일에 저장되었습니다.")
        else:
            # 콘솔에 테이블로 표시
            console.print(f"{folder} 폴더의 최근 변경된 이메일 ({len(emails)}개):")
            
            if not emails:
                console.print("변경된 이메일이 없습니다.")
            else:
                table = _format_email_table(emails, show_body)
                console.print(table)
                
    except BaseError as e:
        logger.exception("델타 쿼리 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("델타 쿼리 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.command()
@click.option("--start-date", "-s", required=True, help="시작 날짜 (YYYY-MM-DD 형식)")
@click.option("--end-date", "-e", help="종료 날짜 (YYYY-MM-DD 형식, 기본값: 시작 날짜와 동일)")
@click.option("--folder", "-f", default="inbox", type=click.Choice(["inbox", "sentItems"]), help="폴더 (inbox 또는 sentItems)")
@click.option("--limit", "-l", default=50, help="최대 결과 수 (기본값: 50개)")
@click.option("--show-body/--no-body", default=True, help="본문 미리보기 표시 여부 (기본값: 표시)")
@click.option("--output", "-o", help="결과를 저장할 JSON 파일 경로")
def date_search(start_date, end_date, folder, limit, show_body, output):
    """특정 날짜 범위의 이메일을 조회합니다 (본문 포함)."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 날짜 형식 변환
        try:
            # 시작 날짜 처리
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            start_iso = f"{start_date}T00:00:00Z"
            
            # 종료 날짜 처리 (지정되지 않은 경우 시작 날짜와 동일)
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_iso = f"{end_date}T23:59:59Z"
            else:
                end_iso = f"{start_date}T23:59:59Z"
                end_dt = start_dt
        except ValueError:
            click.echo("날짜 형식 오류: YYYY-MM-DD 형식으로 입력하세요 (예: 2025-03-01)")
            sys.exit(1)
        
        date_range_str = f"{start_date}"
        if end_date and start_date != end_date:
            date_range_str += f" ~ {end_date}"
        
        # 이메일 조회 (본문 포함)
        if folder == "inbox":
            emails = email_service.get_inbox_emails_with_body(
                start_date=start_iso,
                end_date=end_iso,
                limit=limit
            )
        else:  # sentItems
            emails = email_service.get_sent_emails_with_body(
                start_date=start_iso,
                end_date=end_iso,
                limit=limit
            )
        
        # 결과 표시
        if output:
            # JSON 파일로 저장
            result = []
            for email in emails:
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": f"{email.sender.name} <{email.sender.email}>",
                    "date": (email.received_date or email.sent_date).isoformat() if (email.received_date or email.sent_date) else None,
                    "is_read": email.is_read,
                    "body": email.body_content[:500] + "..." if len(email.body_content) > 500 else email.body_content
                }
                result.append(email_dict)
                
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            click.echo(f"{len(emails)}개의 이메일이 {output} 파일에 저장되었습니다.")
        else:
            # 콘솔에 테이블로 표시
            folder_name = "수신함" if folder == "inbox" else "송신함"
            console.print(f"{date_range_str} 기간의 {folder_name} 이메일 ({len(emails)}개):")
            
            if not emails:
                console.print("해당 기간에 이메일이 없습니다.")
            else:
                table = _format_email_table(emails, show_body)
                console.print(table)
                
    except BaseError as e:
        logger.exception("날짜 검색 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("날짜 검색 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)

@email.command()
@click.argument("search_term")
@click.option("--folder", "-f", help="특정 폴더 내에서만 검색 (기본값: 전체)")
@click.option("--show-body/--no-body", default=False, help="본문 미리보기 표시 여부")
@click.option("--output", "-o", help="결과를 저장할 JSON 파일 경로")
def search(search_term, folder, show_body, output):
    """키워드로 이메일을 검색합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 이메일 검색
        emails = email_service.search_emails(search_term=search_term, folder=folder)
        
        # 결과 표시
        if output:
            # JSON 파일로 저장
            result = []
            for email in emails:
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": f"{email.sender.name} <{email.sender.email}>",
                    "date": (email.received_date or email.sent_date).isoformat() if (email.received_date or email.sent_date) else None,
                    "is_read": email.is_read
                }
                result.append(email_dict)
                
            with open(output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
                
            click.echo(f"검색 결과 {len(emails)}개의 이메일이 {output} 파일에 저장되었습니다.")
        else:
            # 콘솔에 테이블로 표시
            folder_str = f"{folder} 폴더 내 " if folder else ""
            console.print(f"{folder_str}'{search_term}' 검색 결과 ({len(emails)}개):")
            
            if not emails:
                console.print("검색 결과가 없습니다.")
            else:
                table = _format_email_table(emails, show_body)
                console.print(table)
                
    except BaseError as e:
        logger.exception("이메일 검색 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("이메일 검색 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.command()
@click.argument("message_id")
@click.option("--include-attachments/--no-attachments", default=False, help="첨부 파일 포함 여부")
def view(message_id, include_attachments):
    """특정 이메일을 조회합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 이메일 조회
        email_item = email_service.get_email(message_id=message_id, include_attachments=include_attachments)
        
        # 헤더 정보 표시
        console.print(f"[bold]제목:[/bold] {email_item.subject}")
        console.print(f"[bold]발신자:[/bold] {email_item.sender.name} <{email_item.sender.email}>")
        
        # 수신자 정보 표시
        recipients = [f"{r.name} <{r.email}>" for r in email_item.recipients]
        if recipients:
            console.print(f"[bold]수신자:[/bold] {', '.join(recipients)}")
            
        # 참조자 정보 표시
        cc_recipients = [f"{r.name} <{r.email}>" for r in email_item.cc_recipients]
        if cc_recipients:
            console.print(f"[bold]참조:[/bold] {', '.join(cc_recipients)}")
            
        # 날짜 정보 표시
        date_str = ""
        if email_item.received_date:
            date_str = f"수신: {email_item.received_date.strftime('%Y-%m-%d %H:%M:%S')}"
        elif email_item.sent_date:
            date_str = f"발신: {email_item.sent_date.strftime('%Y-%m-%d %H:%M:%S')}"
            
        if date_str:
            console.print(f"[bold]날짜:[/bold] {date_str}")
            
        # 첨부 파일 정보 표시
        if email_item.has_attachments:
            attachments = [f"{a.name} ({a.size} bytes)" for a in email_item.attachments]
            console.print(f"[bold]첨부 파일:[/bold] {', '.join(attachments)}")
            
        # 본문 내용 표시
        console.print("\n[bold]본문:[/bold]")
        console.print(email_item.body_content)
                
    except BaseError as e:
        logger.exception("이메일 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("이메일 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.command()
@click.argument("message_id")
def mark_read(message_id):
    """이메일을 읽음으로 표시합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 읽음 표시
        result = email_service.mark_as_read(message_id=message_id)
        
        if result:
            click.echo(f"메시지 ID {message_id}가 읽음으로 표시되었습니다.")
        else:
            click.echo(f"메시지 ID {message_id}를 읽음으로 표시하지 못했습니다.")
                
    except BaseError as e:
        logger.exception("이메일 읽음 표시 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("이메일 읽음 표시 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.command()
@click.option("--subject", "-s", required=True, help="이메일 제목")
@click.option("--body", "-b", required=True, help="이메일 본문")
@click.option("--to", "-t", required=True, multiple=True, help="수신자 이메일 주소 (여러 명인 경우 반복)")
@click.option("--cc", multiple=True, help="참조 수신자 이메일 주소 (여러 명인 경우 반복)")
@click.option("--bcc", multiple=True, help="숨은 참조 수신자 이메일 주소 (여러 명인 경우 반복)")
@click.option("--body-type", type=click.Choice(["html", "text"]), default="html", help="본문 유형 (기본값: html)")
@click.option("--importance", type=click.Choice(["low", "normal", "high"]), default="normal", help="중요도 (기본값: normal)")
def send(subject, body, to, cc, bcc, body_type, importance):
    """이메일을 발송합니다."""
    try:
        _check_auth()
        
        email_service = EmailService()
        
        # 이메일 발송
        result = email_service.send_email(
            subject=subject,
            body=body,
            recipients=list(to),
            cc_recipients=list(cc) if cc else None,
            bcc_recipients=list(bcc) if bcc else None,
            body_type=body_type,
            importance=importance
        )
        
        if result:
            click.echo(f"이메일이 성공적으로 발송되었습니다.")
            click.echo(f"제목: {subject}")
            click.echo(f"수신자: {', '.join(to)}")
            if cc:
                click.echo(f"참조: {', '.join(cc)}")
            if bcc:
                click.echo(f"숨은 참조: {', '.join(bcc)}")
        else:
            click.echo("이메일 발송에 실패했습니다.")
                
    except BaseError as e:
        logger.exception("이메일 발송 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("이메일 발송 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@email.group()
def filter():
    """필터 관련 명령어"""
    pass


@filter.command(name="list")
def filter_list():
    """필터링할 발신자 목록을 조회합니다."""
    try:
        email_service = EmailService()
        
        # 필터 목록 조회
        filters = email_service.get_filter_senders()
        
        console.print("[bold]필터링할 발신자 목록:[/bold]")
        
        if not filters:
            console.print("등록된 필터가 없습니다.")
        else:
            for i, filter_item in enumerate(filters, 1):
                console.print(f"{i}. {filter_item}")
                
    except BaseError as e:
        logger.exception("필터 목록 조회 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("필터 목록 조회 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@filter.command(name="add")
@click.argument("sender")
def filter_add(sender):
    """필터링할 발신자를 추가합니다."""
    try:
        email_service = EmailService()
        
        # 필터 추가
        email_service.add_filter_sender(sender)
        
        click.echo(f"필터링할 발신자가 추가되었습니다: {sender}")
                
    except BaseError as e:
        logger.exception("필터 추가 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("필터 추가 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


@filter.command(name="remove")
@click.argument("sender")
def filter_remove(sender):
    """필터링할 발신자를 제거합니다."""
    try:
        email_service = EmailService()
        
        # 필터 제거
        result = email_service.remove_filter_sender(sender)
        
        if result:
            click.echo(f"필터링할 발신자가 제거되었습니다: {sender}")
        else:
            click.echo(f"필터링할 발신자 제거 실패 (없음): {sender}")
                
    except BaseError as e:
        logger.exception("필터 제거 중 오류 발생")
        click.echo(f"오류: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.exception("필터 제거 중 예기치 않은 오류 발생")
        click.echo(f"예기치 않은 오류: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    email()
