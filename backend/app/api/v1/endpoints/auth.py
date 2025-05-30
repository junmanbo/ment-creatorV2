# app/api/v1/endpoints/auth.py
"""
인증 관련 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_async_session
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenRefreshResponse, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """사용자 로그인"""
    try:
        auth_service = AuthService()
        return await auth_service.login(db, login_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """토큰 갱신"""
    try:
        auth_service = AuthService()
        token_data = await auth_service.refresh_token(db, refresh_data.refresh_token)
        return TokenRefreshResponse(**token_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e


@router.post("/logout")
async def logout():
    """로그아웃"""
    # JWT는 stateless이므로 클라이언트에서 토큰 삭제
    return {"message": "Successfully logged out"}
