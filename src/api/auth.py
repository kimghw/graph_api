"""인증 API 라우터

이 모듈은 인증 관련 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional

from src.services.auth_service import AuthService
from src.schemas.auth import AuthResult, AuthStatus, UserInfo

# 라우터 생성
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# 서비스 인스턴스
auth_service = AuthService()


def get_auth_service():
    """의존성 주입을 위한 AuthService 인스턴스 제공"""
    return auth_service


@router.get("/status", response_model=AuthStatus)
async def get_auth_status(
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthStatus:
    """현재 인증 상태를 조회합니다.
    
    Returns:
        AuthStatus: 인증 상태 정보
    """
    return auth_service.get_auth_status()


@router.get("/user", response_model=Optional[UserInfo])
async def get_user_info(
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[UserInfo]:
    """현재 인증된 사용자 정보를 조회합니다.
    
    Returns:
        Optional[UserInfo]: 사용자 정보, 인증되지 않은 경우 None
    
    Raises:
        HTTPException: 인증되지 않은 경우
    """
    if not auth_service.is_authenticated():
        raise HTTPException(status_code=401, detail="인증되지 않음")
        
    return auth_service.get_user_info()


@router.post("/interactive", response_model=AuthResult)
async def authenticate_interactive(
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResult:
    """대화형 인증을 수행합니다.
    
    브라우저를 열어 사용자가 Microsoft 계정으로 로그인하는 방식의 인증입니다.
    
    Returns:
        AuthResult: 인증 결과
    """
    result = auth_service.authenticate_interactive()
    
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error_message)
        
    return result


# 디바이스 코드 인증 및 클라이언트 자격 증명 인증은 비활성화
# @router.post("/device", response_model=AuthResult)
# async def authenticate_device(
#     auth_service: AuthService = Depends(get_auth_service)
# ) -> AuthResult:
#     """디바이스 코드 인증을 수행합니다.
#     
#     다른 장치에서 코드를 입력하여 인증하는 방식입니다.
#     
#     Returns:
#         AuthResult: 인증 결과
#     """
#     result = auth_service.authenticate_device()
#     
#     if not result.success:
#         raise HTTPException(status_code=401, detail=result.error_message)
#         
#     return result


# @router.post("/client", response_model=AuthResult)
# async def authenticate_client_credentials(
#     auth_service: AuthService = Depends(get_auth_service)
# ) -> AuthResult:
#     """클라이언트 자격 증명 인증을 수행합니다.
#     
#     사용자 상호 작용 없이 애플리케이션 자격 증명으로 인증하는 방식입니다.
#     
#     Returns:
#         AuthResult: 인증 결과
#     """
#     result = auth_service.authenticate_client_credentials()
#     
#     if not result.success:
#         raise HTTPException(status_code=401, detail=result.error_message)
#         
#     return result


@router.post("/logout", response_model=Dict[str, bool])
async def logout(
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, bool]:
    """로그아웃합니다.
    
    Returns:
        Dict[str, bool]: 로그아웃 성공 여부
    """
    result = auth_service.logout()
    return {"success": result}


@router.get("/token", response_model=Optional[Dict[str, Any]])
async def get_token(
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[Dict[str, Any]]:
    """현재 액세스 토큰을 조회합니다.
    
    Returns:
        Optional[Dict[str, Any]]: 토큰 정보, 인증되지 않은 경우 None
    
    Raises:
        HTTPException: 인증되지 않은 경우
    """
    if not auth_service.is_authenticated():
        raise HTTPException(status_code=401, detail="인증되지 않음")
        
    return auth_service.get_token()
