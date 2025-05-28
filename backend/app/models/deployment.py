"""
배포 관련 모델
"""

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.constants import DeploymentEnvironment, DeploymentStatus


class Deployment(Base):
    """배포 모델"""

    __tablename__ = "deployments"

    # 기본 정보
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    environment = Column(Enum(DeploymentEnvironment), nullable=False)
    version = Column(String(20), nullable=False)

    # 상태 정보
    status = Column(
        Enum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False
    )
    rollback_version = Column(String(20))
    error_message = Column(Text)

    # 설정 정보
    config = Column(JSONB, default={})

    # 배포 정보
    deployed_by = Column(Integer, ForeignKey("users.id"))
    started_at = Column(Integer)  # Unix timestamp
    completed_at = Column(Integer)  # Unix timestamp

    # 관계 (back_populates 없이 단방향만)
    scenario = relationship("Scenario", overlaps="deployments")
    deployer = relationship("User", overlaps="deployments")

    def __repr__(self) -> str:
        return f"<Deployment(id={self.id}, scenario_id={self.scenario_id}, environment='{self.environment}', status='{self.status}')>"
