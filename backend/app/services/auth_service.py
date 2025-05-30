"""
인증 서비스
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import security
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.logger import logger


class AuthService:
    """인증 서비스"""

    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str
    ) -> User | None:
        """사용자 인증"""
        try:
            # 사용자명 또는 이메일로 조회
            result = await db.execute(
                select(User).where(
                    (User.username == username) | (User.email == username)
                )
            )
            user = result.scalars().first()

            if not user:
                logger.warning(
                    "Authentication failed: user not found", username=username
                )
                return None

            if not user.is_active:
                logger.warning(
                    "Authentication failed: user inactive", username=username
                )
                return None

            # 비밀번호 확인
            if not security.verify_password(password, user.hashed_password):
                logger.warning(
                    "Authentication failed: wrong password", username=username
                )
                return None

            # 마지막 로그인 시간 업데이트
            user.last_login_at = datetime.utcnow()
            await db.commit()

            logger.info(
                "User authenticated successfully", user_id=user.id, username=username
            )
            return user

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError("인증 처리 중 오류가 발생했습니다.") from e

    async def login(self, db: AsyncSession, login_data: LoginRequest) -> TokenResponse:
        """로그인"""
        user = await self.authenticate_user(
            db, login_data.username, login_data.password
        )

        if not user:
            raise AuthenticationError("사용자명 또는 비밀번호가 올바르지 않습니다.")

        # 토큰 생성
        access_token = security.create_access_token(subject=user.id)
        refresh_token = security.create_refresh_token(subject=user.id)

        from app.schemas.user import UserResponse

        user_response = UserResponse.model_validate(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response,
        )

    async def refresh_token(
        self, db: AsyncSession, refresh_token: str
    ) -> dict[str, Any]:
        """토큰 갱신"""
        user_id = security.verify_token(refresh_token, token_type="refresh")

        if not user_id:
            raise AuthenticationError("유효하지 않은 리프레시 토큰입니다.")

        # 사용자 조회
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()

        if not user or not user.is_active:
            raise AuthenticationError("사용자를 찾을 수 없거나 비활성 상태입니다.")

        # 새 액세스 토큰 생성
        new_access_token = security.create_access_token(subject=user.id)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def get_current_user(self, db: AsyncSession, token: str) -> User:
        """현재 사용자 조회"""
        user_id = security.verify_token(token)

        if not user_id:
            raise AuthenticationError("유효하지 않은 토큰입니다.")

        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()

        if not user:
            raise AuthenticationError("사용자를 찾을 수 없습니다.")

        if not user.is_active:
            raise AuthenticationError("비활성 사용자입니다.")

        return user
