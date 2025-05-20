#!/usr/bin/env python3
"""
특정 날짜 범위의 이메일 본문 조회 시각화
"""

import json
import sys
from datetime import datetime, timezone
from pprint import pprint

from src.services.email_service import EmailService
from src.infra.graph_gateway import GraphApiGateway
from src.schemas.email import EmailDto, EmailProcessingOptions


def main():
    """메인 함수"""
    try:
        # 이메일 서비스 초기화
        email_service = EmailService()
        
        # 날짜 범위 설정 (2025년 3월 1일 ~ 3월 10일)
        start_date = "2025-03-01T00:00:00Z"  # ISO 8601 형식 문자열
        end_date = "2025-03-10T23:59:59Z"    # ISO 8601 형식 문자열
        
        print(f"[1] 이메일 검색 - 날짜 범위: {start_date[:10]} ~ {end_date[:10]}")
        
        # 수신함 이메일 조회 (본문 포함)
        emails = email_service.get_inbox_emails_with_body(
            start_date=start_date,
            end_date=end_date,
            limit=50,  # 최대 50개 조회
            filter_senders=True,  # 필터링 적용
            convert_html_to_text=True  # HTML을 텍스트로 변환
        )
        
        print(f"\n총 {len(emails)}개의 이메일이 조회되었습니다.\n")
        
        if emails:
            print("[2] 조회된 이메일 목록")
            print("-" * 50)
            
            # 이메일 목록 출력
            for idx, email in enumerate(emails[:10], 1):
                received_date_str = email.received_date.strftime('%Y-%m-%d %H:%M') if email.received_date else "날짜 없음"
                print(f"{idx}. 제목: {email.subject}")
                print(f"   발신자: {email.sender.name} <{email.sender.email}>")
                print(f"   수신일: {received_date_str}")
                print(f"   본문 미리보기: {email.body_content[:80]}...")
                print("-" * 50)
                
            if len(emails) > 10:
                print(f"... 외 {len(emails) - 10}개 추가 이메일")
            
            # 첫 번째 이메일 상세 정보
            print("\n[3] 첫 번째 이메일 상세 정보")
            first_email = emails[0]
            
            # 기본 정보 출력
            print("\n[이메일 기본 정보]")
            print(f"ID: {first_email.id}")
            print(f"제목: {first_email.subject}")
            print(f"발신자: {first_email.sender.name} <{first_email.sender.email}>")
            
            # 수신자 정보
            if first_email.recipients:
                recipients_str = ", ".join([f"{r.name} <{r.email}>" for r in first_email.recipients])
                print(f"수신자: {recipients_str}")
                
            # 날짜 및 상태 정보
            if first_email.received_date:
                print(f"수신 날짜: {first_email.received_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"읽음 여부: {'읽음' if first_email.is_read else '읽지 않음'}")
            print(f"중요도: {first_email.importance}")
            print(f"본문 유형: {first_email.body_type}")
            print(f"첨부파일: {'있음' if first_email.has_attachments else '없음'}")
            
            # 본문 전체 내용
            print("\n[이메일 본문 내용]")
            print("-" * 50)
            print(first_email.body_content)
            print("-" * 50)
            
            # JSON 형태로 출력
            print("\n[4] 이메일 JSON 형태 예시")
            user_dict = {
                "id": first_email.id,
                "subject": first_email.subject,
                "sender": f"{first_email.sender.name} <{first_email.sender.email}>",
                "date": first_email.received_date.isoformat() if first_email.received_date else None,
                "is_read": first_email.is_read,
                "body": first_email.body_content[:200] + "..." if len(first_email.body_content) > 200 else first_email.body_content
            }
            print(json.dumps(user_dict, ensure_ascii=False, indent=2))
        else:
            print("해당 날짜 범위에 이메일이 없습니다.")
        
        return 0
        
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
