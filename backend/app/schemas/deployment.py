"""
배포 스키마
"""

from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, TimestampSchema
from app.schemas.common import UserBasic
from app.utils.constants import DeploymentEnvironment, DeploymentStatus


class DeploymentBase(BaseSchema):
    """배포 기본 스키마"""

    environment: DeploymentEnvironment = Field(..., description="배포 환경")
    version: str = Field(..., description="배포 버전")
    config: dict[str, Any] | None = Field(default_factory=dict, description="배포 설정")


class DeploymentCreate(DeploymentBase):
    """배포 생성 스키마"""

    scenario_id: int = Field(..., description="시나리오 ID")


class DeploymentUpdate(BaseSchema):
    """배포 수정 스키마"""

    status: DeploymentStatus | None = None
    rollback_version: str | None = None
    error_message: str | None = None


class DeploymentResponse(DeploymentBase, IDMixin, TimestampSchema):
    """배포 응답 스키마"""

    scenario_id: int
    status: DeploymentStatus
    rollback_version: str | None = None
    error_message: str | None = None
    deployed_by: UserBasic | None = None
    started_at: int | None = None
    completed_at: int | None = None

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseSchema):
    """배포 목록 응답"""

    items: list[DeploymentResponse]
    page: int
    size: int
    total: int
    pages: int


class DeploymentRollbackRequest(BaseSchema):
    """배포 롤백 요청"""

    rollback_version: str = Field(..., description="롤백할 버전")
    reason: str | None = Field(None, description="롤백 사유")
