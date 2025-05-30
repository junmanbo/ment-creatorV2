"""
FastAPI 애플리케이션 메인 파일 (기본 테스트 버전)
"""
from typing import Any, Dict

from fastapi import FastAPI

from app.core.config import settings
from app.utils.logger import logger


def create_application() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )
    
    # 기본 라우터만 등록
    setup_basic_routers(app)
    
    logger.info("FastAPI application created successfully")
    
    return app


def setup_basic_routers(app: FastAPI) -> None:
    """기본 라우터 설정"""
    
    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """헬스체크 엔드포인트"""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }
    
    @app.get("/")
    async def root() -> Dict[str, str]:
        """루트 엔드포인트"""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs",
        }
    
    # API v1 기본 엔드포인트들
    @app.get(f"{settings.API_V1_STR}/")
    async def api_v1_root() -> Dict[str, str]:
        """API v1 루트"""
        return {"message": "API v1 is running", "version": settings.VERSION}
    
    @app.get(f"{settings.API_V1_STR}/status")
    async def api_status() -> Dict[str, Any]:
        """API 상태 확인"""
        return {
            "api_version": "v1",
            "status": "operational",
            "features": [
                "Authentication",
                "User Management", 
                "Scenario Management",
                "Voice Actor Management",
                "TTS Generation"
            ]
        }
    
    # 간단한 테스트 엔드포인트들 추가
    @app.get(f"{settings.API_V1_STR}/test/ping")
    async def ping() -> Dict[str, str]:
        """핑 테스트"""
        return {"message": "pong"}
    
    @app.post(f"{settings.API_V1_STR}/test/echo")
    async def echo(data: Dict[str, Any]) -> Dict[str, Any]:
        """에코 테스트"""
        return {"received": data, "timestamp": "2025-05-31T00:00:00Z"}


# FastAPI 앱 인스턴스 생성
app = create_application()
