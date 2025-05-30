"""
인증 관련 스키마
"""
from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema
from app.utils.constants import UserRole


class LoginRequest(BaseSchema):
    """로그인 요청 스키마"""
    
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    password: str = Field(..., min_length=6, description="비밀번호")


class TokenResponse(BaseSchema):
    """토큰 응답 스키마"""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfo"


class TokenRefreshResponse(BaseSchema):
    """토큰 갱신 응답 스키마"""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseSchema):
    """토큰 갱신 요청 스키마"""
    
    refresh_token: str


class UserInfo(BaseSchema):
    """사용자 정보 스키마"""
    
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: UserRole
    department: Optional[str] = None


# Forward reference 해결
TokenResponse.model_rebuild()
