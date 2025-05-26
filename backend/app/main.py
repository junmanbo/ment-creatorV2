# app/main.py
"""
FastAPI 애플리케이션 메인 파일
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import BaseCustomException
from app.core.middleware import setup_middleware
from app.db.init_db import check_database_connection, init_database
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """애플리케이션 생명주기 관리"""

    # 시작 시 실행
    logger.info("🚀 Starting Insurance ARS Manager API")

    # 데이터베이스 연결 확인
    db_connected = await check_database_connection()
    if not db_connected:
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")

    # 데이터베이스 초기화
    if settings.ENVIRONMENT in ["development", "testing"]:
        await init_database()

    logger.info("✅ Application startup completed")

    yield

    # 종료 시 실행
    logger.info("🛑 Shutting down Insurance ARS Manager API")


def create_application() -> FastAPI:
    """FastAPI 애플리케이션 생성"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # 미들웨어 설정
    setup_middleware(app)

    # 라우터 등록
    setup_routers(app)

    # 예외 핸들러 등록
    setup_exception_handlers(app)

    return app


def setup_routers(app: FastAPI) -> None:
    """라우터 설정"""

    # API v1 라우터는 나중에 구현
    # from app.api.v1.api import api_router
    # app.include_router(api_router, prefix=settings.API_V1_STR)

    # 헬스체크 엔드포인트
    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """헬스체크 엔드포인트"""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # 루트 엔드포인트
    @app.get("/")
    async def root() -> dict[str, str]:
        """루트 엔드포인트"""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "docs_url": f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        }


def setup_exception_handlers(app: FastAPI) -> None:
    """예외 핸들러 설정"""

    @app.exception_handler(BaseCustomException)
    async def custom_exception_handler(
        request: Request, exc: BaseCustomException
    ) -> JSONResponse:
        """커스텀 예외 핸들러"""

        logger.error(
            "Custom exception occurred",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "timestamp": "2025-05-25T10:30:00Z",  # UTC 시간으로 교체 필요
                "request_id": request.headers.get("X-Request-ID", ""),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """HTTP 예외 핸들러"""

        logger.warning(
            "HTTP exception occurred",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "details": {},
                },
                "timestamp": "2025-05-25T10:30:00Z",  # UTC 시간으로 교체 필요
                "request_id": request.headers.get("X-Request-ID", ""),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """검증 예외 핸들러"""

        logger.warning(
            "Validation error occurred",
            errors=exc.errors(),
            path=request.url.path,
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "입력 데이터 검증에 실패했습니다.",
                    "details": {"validation_errors": exc.errors()},
                },
                "timestamp": "2025-05-25T10:30:00Z",  # UTC 시간으로 교체 필요
                "request_id": request.headers.get("X-Request-ID", ""),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """일반 예외 핸들러"""

        logger.error(
            "Unexpected error occurred",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            exc_info=True,
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "내부 서버 오류가 발생했습니다.",
                    "details": {}
                    if settings.ENVIRONMENT == "production"
                    else {"error": str(exc)},
                },
                "timestamp": "2025-05-25T10:30:00Z",  # UTC 시간으로 교체 필요
                "request_id": request.headers.get("X-Request-ID", ""),
            },
        )


# FastAPI 앱 인스턴스 생성
app = create_application()
