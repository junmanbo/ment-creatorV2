# app/api/v1/endpoints/deployments.py
"""
배포 관리 엔드포인트
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_operator_user
from app.api.dependencies.database import get_async_session
from app.api.dependencies.pagination import PaginationParams
from app.models.user import User
from app.schemas.deployment import (
    DeploymentCreate,
    DeploymentListResponse,
    DeploymentResponse,
    DeploymentRollbackRequest,
)
from app.services.deployment_service import DeploymentService
from app.utils.constants import DeploymentEnvironment, DeploymentStatus

router = APIRouter()


@router.get("/", response_model=DeploymentListResponse)
async def get_deployments(
    pagination: PaginationParams = Depends(),
    environment: Optional[DeploymentEnvironment] = Query(None, description="환경 필터"),
    status_filter: Optional[DeploymentStatus] = Query(None, description="상태 필터"),
    scenario_id: Optional[int] = Query(None, description="시나리오 ID 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """배포 목록 조회"""
    deployment_service = DeploymentService()
    deployments, total = await deployment_service.search_deployments(
        db,
        environment=environment,
        status=status_filter,
        scenario_id=scenario_id,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return DeploymentListResponse(
        items=[DeploymentResponse.model_validate(deployment) for deployment in deployments],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """배포 상태 조회"""
    deployment_service = DeploymentService()
    deployment = await deployment_service.get_or_404(db, deployment_id)
    return DeploymentResponse.model_validate(deployment)


@router.post("/scenarios/{scenario_id}/deploy", response_model=DeploymentResponse, status_code=status.HTTP_201_CREATED)
async def deploy_scenario(
    scenario_id: int,
    deployment_in: DeploymentCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """시나리오 배포"""
    deployment_service = DeploymentService()
    deployment = await deployment_service.create_deployment(
        db,
        scenario_id=scenario_id,
        deployment_in=deployment_in,
        deployed_by=current_user.id
    )
    return DeploymentResponse.model_validate(deployment)


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    deployment_id: int,
    rollback_request: DeploymentRollbackRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """배포 롤백"""
    deployment_service = DeploymentService()
    
    # 기존 배포 조회
    deployment = await deployment_service.get_or_404(db, deployment_id)
    
    if deployment.status != DeploymentStatus.DEPLOYED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="배포된 상태가 아닙니다."
        )
    
    # 롤백 실행
    rollback_deployment = await deployment_service.rollback_deployment(
        db,
        deployment_id=deployment_id,
        rollback_version=rollback_request.rollback_version,
        performed_by=current_user.id
    )
    
    return DeploymentResponse.model_validate(rollback_deployment)


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_deployment(
    deployment_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """배포 취소"""
    deployment_service = DeploymentService()
    deployment = await deployment_service.get_or_404(db, deployment_id)
    
    if deployment.status not in [DeploymentStatus.PENDING, DeploymentStatus.DEPLOYING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="취소할 수 없는 상태입니다."
        )
    
    await deployment_service.cancel_deployment(db, deployment_id)


@router.get("/environments/{environment}/status")
async def get_environment_status(
    environment: DeploymentEnvironment,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """환경별 배포 상태 조회"""
    deployment_service = DeploymentService()
    status_info = await deployment_service.get_environment_status(db, environment)
    return {
        "environment": environment,
        "active_deployments": status_info["active_count"],
        "pending_deployments": status_info["pending_count"],
        "last_deployment": status_info["last_deployment"],
        "health_status": status_info["health_status"]
    }
