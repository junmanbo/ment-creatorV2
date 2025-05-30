# app/api/v1/endpoints/users.py
"""
사용자 관리 엔드포인트
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_admin_user, get_current_active_user, get_manager_user
from app.api.dependencies.database import get_async_session
from app.api.dependencies.pagination import PaginationParams, SearchParams
from app.models.user import User
from app.schemas.user import (
    UserChangePassword,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService
from app.utils.constants import UserRole

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def get_users(
    pagination: PaginationParams = Depends(),
    search: SearchParams = Depends(),
    role: Optional[UserRole] = Query(None, description="역할 필터"),
    department: Optional[str] = Query(None, description="부서 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)  # 관리자/매니저만 접근
):
    """사용자 목록 조회"""
    user_service = UserService()
    users, total = await user_service.search_users(
        db,
        search=search.search,
        role=role,
        department=department,
        is_active=is_active,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """현재 사용자 정보 조회"""
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)
):
    """특정 사용자 조회"""
    user_service = UserService()
    user = await user_service.get_or_404(db, user_id)
    return UserResponse.model_validate(user)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)  # 관리자만 생성 가능
):
    """새 사용자 생성"""
    user_service = UserService()
    user = await user_service.create_user(db, user_in=user_in)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """사용자 정보 수정"""
    # 자신의 정보이거나 관리자/매니저인 경우만 수정 가능
    if user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user_service = UserService()
    user = await user_service.update_user(db, user_id=user_id, user_in=user_in)
    return UserResponse.model_validate(user)


@router.put("/me/password", response_model=UserResponse)
async def change_password(
    password_data: UserChangePassword,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """비밀번호 변경"""
    user_service = UserService()
    user = await user_service.change_password(
        db, 
        user_id=current_user.id, 
        password_data=password_data
    )
    return UserResponse.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """사용자 활성화"""
    user_service = UserService()
    user = await user_service.activate_user(db, user_id)
    return UserResponse.model_validate(user)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """사용자 비활성화"""
    user_service = UserService()
    user = await user_service.deactivate_user(db, user_id)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """사용자 삭제"""
    user_service = UserService()
    await user_service.delete(db, id=user_id)
