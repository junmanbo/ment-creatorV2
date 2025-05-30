"""
사용자 관련 스키마
"""
from typing import List, Optional

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, IDMixin, PaginationSchema, TimestampMixin
from app.utils.constants import UserRole


class UserBase(BaseSchema):
    """사용자 기본 스키마"""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.OPERATOR
    department: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    
    password: str = Field(..., min_length=6, description="비밀번호")


class UserUpdate(BaseSchema):
    """사용자 수정 스키마"""
    
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserChangePassword(BaseSchema):
    """비밀번호 변경 스키마"""
    
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=6, description="새 비밀번호")


class UserResponse(IDMixin, TimestampMixin, UserBase):
    """사용자 응답 스키마"""
    
    is_active: bool
    last_login_at: Optional[str] = None


class UserListResponse(PaginationSchema):
    """사용자 목록 응답 스키마"""
    
    items: List[UserResponse]
