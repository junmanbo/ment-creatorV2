"""
로깅 설정
"""

import logging
import sys
from typing import Any

import structlog
from structlog import get_logger

from app.core.config import settings


def setup_logging() -> None:
    """로깅 설정 초기화"""

    # 로그 레벨 설정
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # 기본 로깅 설정
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # structlog 설정
    if settings.LOG_FORMAT == "json":
        # JSON 형식 로깅 (운영 환경)
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_logger_name,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            cache_logger_on_first_use=True,
        )
    else:
        # 개발 환경용 컬러 로깅
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.add_logger_name,
                structlog.dev.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(),
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            cache_logger_on_first_use=True,
        )


# 로깅 설정 초기화
setup_logging()

# 로거 인스턴스
logger = get_logger("ars_manager")


def log_api_call(
    method: str, path: str, user_id: int | None = None, **kwargs: Any
) -> None:
    """API 호출 로깅"""
    logger.info("API call", method=method, path=path, user_id=user_id, **kwargs)


def log_business_event(
    event: str,
    user_id: int | None = None,
    details: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    """비즈니스 이벤트 로깅"""
    logger.info(
        "Business event", event=event, user_id=user_id, details=details or {}, **kwargs
    )


def log_error(
    error: Exception, context: dict[str, Any] | None = None, **kwargs: Any
) -> None:
    """에러 로깅"""
    logger.error(
        "Error occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        **kwargs,
        exc_info=True,
    )
