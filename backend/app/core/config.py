# app/core/config.py
"""
애플리케이션 설정 관리
"""

import secrets
from typing import Any

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 기본 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Insurance ARS Manager"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "손해보험 콜센터 ARS 시나리오 관리 및 Voice Cloning TTS 시스템"

    # 환경 설정
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # 보안 설정
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS 설정
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list | str):
            return v
        raise ValueError(v)

    # 데이터베이스 설정
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "insurance_ars"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: PostgresDsn | None = None
    DATABASE_URL_SYNC: str | None = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    @validator("DATABASE_URL_SYNC", pre=True)
    def assemble_sync_db_connection(cls, v: str | None, values: dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:"
            f"{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"
        )

    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379/0"

    # 파일 저장 설정
    UPLOAD_DIR: str = "./uploads"
    AUDIO_DIR: str = "./audio_files"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_EXTENSIONS: list[str] = [".wav", ".mp3", ".flac", ".ogg"]

    # TTS 설정
    TTS_MODEL_PATH: str = "./models"
    TTS_OUTPUT_PATH: str = "./audio_files"
    TTS_SAMPLE_RATE: int = 22050
    TTS_MAX_TEXT_LENGTH: int = 1000
    TTS_GENERATION_TIMEOUT: int = 300  # 5분

    # 페이징 설정
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # 이메일 설정 (선택사항)
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    # 모니터링 설정
    SENTRY_DSN: HttpUrl | None = None

    # Rate Limiting 설정
    RATE_LIMIT_GENERAL: str = "1000/hour"
    RATE_LIMIT_TTS: str = "100/hour"
    RATE_LIMIT_UPLOAD: str = "50/hour"
    RATE_LIMIT_SIMULATION: str = "200/hour"

    # 배포 설정
    DEPLOYMENT_ENVIRONMENTS: list[str] = ["development", "staging", "production"]
    DEFAULT_DEPLOYMENT_TIMEOUT: int = 300  # 5분

    # 보안 헤더 설정
    SECURE_HEADERS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()


# 환경별 설정 검증
def get_environment_settings() -> Settings:
    """환경별 설정 반환 및 검증"""
    if settings.ENVIRONMENT == "production":
        # 운영 환경 필수 설정 검증
        required_prod_settings = ["SECRET_KEY", "DATABASE_URL", "POSTGRES_PASSWORD"]

        for setting in required_prod_settings:
            if not getattr(settings, setting, None):
                raise ValueError(f"Missing required production setting: {setting}")

        # 운영 환경 보안 설정
        settings.DEBUG = False
        settings.SECURE_HEADERS = True

    elif settings.ENVIRONMENT == "testing":
        # 테스트 환경 설정
        settings.DATABASE_URL = "sqlite+aiosqlite:///./test.db"
        settings.DATABASE_URL_SYNC = "sqlite:///./test.db"

    return settings
