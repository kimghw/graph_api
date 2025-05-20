#!/usr/bin/env python3
"""
이메일 HTML 변환 테스트 스크립트
"""

import json
import sys
from datetime import datetime
from pprint import pprint

from src.schemas.email import EmailDto, EmailProcessingOptions


def main():
    """메인 함수"""
    try:
        # 테스트용 HTML 샘플 데이터 준비
        sample_html = """
        <div>
            <table>
                <tr>
                    <th>Column 1</th>
                    <th>Column 2</th>
                </tr>
                <tr>
                    <td>Data 1</td>
                    <td>Data 2</td>
                </tr>
            </table>
            <hr/>
            <div>
                |  
                ---  
                
                | |   
                ---  
                Let's get you signed in  
                Sign in with the secure link below  
                | <a href="https://console.anthropic.com/magic-link#4c2e8047affe7d442df8d29405aa37a0:a2ltZ2h3QGtycy5jby5rcg==">Sign in to Anthropic Console</a>  
                ---  
                If you didn't request this email, you can safely ignore it.
            </div>
            <hr/>
            <div>일반 텍스트 내용도 포함</div>
            <p>This is a <strong>test</strong> email with some <a href="https://example.com">links</a></p>
        </div>
        """
        
        # API 응답 형태의 테스트 데이터 생성
        test_email_data = {
            "id": "test-email-id",
            "subject": "테스트 이메일",
            "from": {
                "emailAddress": {
                    "name": "테스트 발신자",
                    "address": "sender@example.com"
                }
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "name": "테스트 수신자",
                        "address": "recipient@example.com"
                    }
                }
            ],
            "receivedDateTime": "2023-01-01T00:00:00Z",
            "body": {
                "contentType": "html",
                "content": sample_html
            }
        }
        
        print("[1] 테스트 HTML 데이터:")
        print("-" * 50)
        print(sample_html[:200] + "..." if len(sample_html) > 200 else sample_html)
        print("-" * 50)
        
        # 2. EmailDto로 변환 처리
        print("\n[2] HTML 데이터를 EmailDto로 변환 (전처리 적용)")
        
        # html2text 패키지 확인
        try:
            import html2text
            print("html2text 패키지가 정상적으로 임포트됨")
            print(f"html2text 버전: {html2text.__version__}")
        except ImportError:
            print("html2text 패키지를 임포트할 수 없습니다!")
        
        # 기본 처리 옵션 (HTML → 텍스트 변환 활성화)
        processing_options = EmailProcessingOptions(
            convert_html_to_text=True,
            include_body=True
        )
        
        # EmailDto로 변환
        email_dto = EmailDto.from_dict(test_email_data, processing_options)
        
        # 변환된 본문 출력
        print("\n[3] 변환 결과 (텍스트 본문):")
        print("-" * 50)
        print(email_dto.body_content)
        print("-" * 50)
        
        # 기본 처리 옵션 (HTML → 텍스트 변환 비활성화 - 비교용)
        print("\n[4] 비교: HTML 변환 비활성화")
        no_convert_options = EmailProcessingOptions(
            convert_html_to_text=False,
            include_body=True
        )
        
        # EmailDto로 변환 (변환 비활성화)
        no_convert_dto = EmailDto.from_dict(test_email_data, no_convert_options)
        
        # 원본 HTML (처리되지 않은) 출력
        print("-" * 50)
        print(f"원본 HTML 길이: {len(no_convert_dto.body_content)} 자")
        print(f"변환된 텍스트 길이: {len(email_dto.body_content)} 자")
        print("-" * 50)
        
        # EmailDto 객체 JSON 형식으로 출력
        print("\n[5] 최종 EmailDto JSON 변환 결과:")
        print("-" * 50)
        
        # EmailDto를 딕셔너리로 변환
        dto_dict = {
            "id": email_dto.id,
            "subject": email_dto.subject,
            "body_content": email_dto.body_content[:200] + "..." if len(email_dto.body_content) > 200 else email_dto.body_content,
            "body_type": email_dto.body_type,
            "sender": {
                "email": email_dto.sender.email,
                "name": email_dto.sender.name,
                "type": email_dto.sender.type
            },
            "recipients": [{
                "email": recipient.email,
                "name": recipient.name,
                "type": recipient.type
            } for recipient in email_dto.recipients],
            "received_date": email_dto.received_date.isoformat() if email_dto.received_date else None,
            "is_read": email_dto.is_read
        }
        
        # JSON 출력
        print(json.dumps(dto_dict, ensure_ascii=False, indent=2))
        print("-" * 50)
        
        return 0
        
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
