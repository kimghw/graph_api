"""FastAPI 애플리케이션

이 모듈은 FastAPI 애플리케이션 인스턴스를 생성하고 라우터를 등록합니다.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.logging_config import LoggerFactory
from src.infra.config import Config
from src.api.auth import router as auth_router

# 로거 설정
logger = LoggerFactory.get_logger(__name__)

# FastAPI 인스턴스 생성
app = FastAPI(
    title="Graph API",
    description="Microsoft Graph API와 상호작용하는 API 서비스",
    version="0.1.0",
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 출처를 지정해야 함
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router)


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "Graph API 서비스가 실행 중입니다",
        "docs_url": "/docs",
    }


def start():
    """API 서버를 시작합니다."""
    logger.info(f"API 서버를 시작합니다. 포트: {Config.API_PORT}")
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=Config.API_PORT,
        reload=True,
    )


if __name__ == "__main__":
    start()
