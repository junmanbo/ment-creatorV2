"""
보안 관련 유틸리티
"""

import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """보안 관리 클래스"""

    @staticmethod
    def create_access_token(
        subject: Union[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """액세스 토큰 생성"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(subject: Union[str, Any]) -> str:
        """리프레시 토큰 생성"""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[str]:
        """토큰 검증"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            # 토큰 타입 검증
            if payload.get("type") != token_type:
                return None
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)

    @staticmethod
    def generate_reset_token() -> str:
        """비밀번호 재설정 토큰 생성"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_api_key() -> str:
        """API 키 생성"""
        return secrets.token_urlsafe(32)


# 보안 관리자 인스턴스
security = SecurityManager()
