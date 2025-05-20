"""이메일 API 라우터

이 모듈은 이메일 관련 API 엔드포인트를 제공합니다.
get_inbox_emails_with_body 함수만 노출됩니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Union
from datetime import datetime

from src.services.email_service import EmailService
from src.schemas.email import EmailDto
from src.utils.exceptions import EmailProcessingError, GraphApiError

# 라우터 생성
router = APIRouter(
    prefix="/email",
    tags=["email"],
    responses={404: {"description": "Not found"}},
)

# 서비스 인스턴스
email_service = EmailService()


def get_email_service():
    """의존성 주입을 위한 EmailService 인스턴스 제공"""
    return email_service


@router.get("/inbox", response_model=List[EmailDto])
async def get_inbox_emails(
    start_date: Optional[str] = Query(None, description="조회 시작 날짜 (ISO 8601 형식, 예: 2025-03-01T00:00:00Z)"),
    end_date: Optional[str] = Query(None, description="조회 종료 날짜 (ISO 8601 형식, 예: 2025-03-11T23:59:59Z)"),
    days: Optional[int] = Query(None, description="조회할 일수 (start_date가 None일 경우에만 사용)"),
    limit: int = Query(1000, description="최대 결과 수"),
    filter_senders: bool = Query(True, description="발신자 필터링 적용 여부"),
    convert_html_to_text: bool = Query(True, description="HTML 본문을 텍스트로 변환할지 여부"),
    email_service: EmailService = Depends(get_email_service)
) -> List[EmailDto]:
    """수신함 이메일을 본문과 함께 조회합니다.
    
    Args:
        start_date: 조회 시작 날짜 (ISO 8601 형식)
        end_date: 조회 종료 날짜 (ISO 8601 형식)
        days: 조회할 일수 (start_date가 None일 경우에만 사용)
        limit: 최대 결과 수
        filter_senders: 발신자 필터링 적용 여부
        convert_html_to_text: HTML 본문을 텍스트로 변환할지 여부
        
    Returns:
        List[EmailDto]: 이메일 DTO 리스트 (본문 포함)
        
    Raises:
        HTTPException: API 요청 처리 중 오류 발생 시
    """
    try:
        return email_service.get_inbox_emails_with_body(
            start_date=start_date,
            end_date=end_date,
            days=days,
            limit=limit,
            filter_senders=filter_senders,
            convert_html_to_text=convert_html_to_text
        )
    except GraphApiError as e:
        # Graph API 오류 처리
        raise HTTPException(status_code=502, detail=f"Graph API 오류: {str(e)}")
    except EmailProcessingError as e:
        # 이메일 처리 오류 처리
        raise HTTPException(status_code=500, detail=f"이메일 처리 오류: {str(e)}")
    except Exception as e:
        # 기타 오류 처리
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
