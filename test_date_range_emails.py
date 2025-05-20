#!/usr/bin/env python3
"""
특정 날짜 범위의 이메일 본문 조회 테스트
"""

import json
import sys
from datetime import datetime, timezone
from pprint import pprint

from src.services.email_service import EmailService


def main():
    """메인 함수"""
    try:
        # 이메일 서비스 초기화
        email_service = EmailService()
        
        # 방법 1: datetime 객체로 날짜 범위 설정 (2025년 3월 1일 ~ 3월 11일)
        # start_date = datetime(2025, 3, 1, tzinfo=timezone.utc)
        # end_date = datetime(2025, 3, 11, 23, 59, 59, tzinfo=timezone.utc)
        
        # 방법 2: ISO 8601 형식 문자열로 날짜 범위 설정 (권장)
        start_date = "2025-03-01T00:00:00Z"  # ISO 8601 형식 문자열
        end_date = "2025-03-10T23:59:59Z"    # ISO 8601 형식 문자열
        
        print(f"테스트 날짜 범위: {start_date[:10]} ~ {end_date[:10]}")
        
        # 수신함 이메일 조회 (본문 포함)
        emails = email_service.get_inbox_emails_with_body(
            start_date=start_date,
            end_date=end_date,
            limit=100,  # 최대 100개 조회
            filter_senders=True,  # 필터링 적용
            convert_html_to_text=True  # HTML을 텍스트로 변환
        )
        
        print(f"\n총 {len(emails)}개의 이메일이 조회되었습니다.\n")
        
        # 조회된 이메일이 있을 경우 결과 출력
        if emails:
            print("조회된 이메일 목록:")
            print("-" * 50)
            
            for idx, email in enumerate(emails[:10], 1):  # 최대 10개만 표시
                received_date_str = email.received_date.strftime('%Y-%m-%d %H:%M') if email.received_date else "날짜 없음"
                body_preview = email.body_content[:100] + "..." if len(email.body_content) > 100 else email.body_content
                
                print(f"{idx}. 제목: {email.subject}")
                print(f"   발신자: {email.sender.name} <{email.sender.email}>")
                print(f"   수신일: {received_date_str}")
                print(f"   본문: {body_preview}")
                print("-" * 50)
                
            if len(emails) > 10:
                print(f"... 외 {len(emails) - 10}개 추가 이메일")
            
            # 첫 번째 이메일 상세 정보 (전체 본문 포함)
            print("\n첫 번째 이메일 상세 정보:")
            print("-" * 50)
            
            first_email = emails[0]
            
            print(f"제목: {first_email.subject}")
            print(f"발신자: {first_email.sender.name} <{first_email.sender.email}>")
            
            if first_email.recipients:
                recipients_str = ", ".join([f"{r.name} <{r.email}>" for r in first_email.recipients])
                print(f"수신자: {recipients_str}")
                
            if first_email.cc_recipients:
                cc_str = ", ".join([f"{r.name} <{r.email}>" for r in first_email.cc_recipients])
                print(f"참조: {cc_str}")
                
            print(f"수신일: {first_email.received_date.strftime('%Y-%m-%d %H:%M:%S') if first_email.received_date else '날짜 없음'}")
            print(f"읽음여부: {'읽음' if first_email.is_read else '읽지 않음'}")
            print(f"중요도: {first_email.importance}")
            print(f"본문 유형: {first_email.body_type}")
            print(f"첨부파일: {'있음' if first_email.has_attachments else '없음'}")
            
            print("\n본문 내용 (전체):")
            print("-" * 50)
            print(first_email.body_content)
            print("-" * 50)
        else:
            print("이 기간에 해당하는 이메일이 없습니다.")
        
        return 0
        
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
