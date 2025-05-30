"""
인증 의존성
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_async_session
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.constants import UserRole

# Bearer 토큰 스키마
security = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """현재 사용자 조회"""
    try:
        auth_service = AuthService()
        user = await auth_service.get_current_user(db, token.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """현재 활성 사용자 조회"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_roles(*allowed_roles: UserRole):
    """특정 역할 필요"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


# 역할별 의존성
get_admin_user = require_roles(UserRole.ADMIN)
get_manager_user = require_roles(UserRole.ADMIN, UserRole.MANAGER)
get_operator_user = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATOR)
