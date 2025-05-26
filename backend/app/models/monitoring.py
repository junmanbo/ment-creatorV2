# app/models/monitoring.py
"""
모니터링 관련 모델
"""

from sqlalchemy import Column, Float, String
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class SystemMetric(Base):
    """시스템 메트릭"""

    __tablename__ = "system_metrics"

    # 기본 정보
    metric_type = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))

    # 태그 정보
    tags = Column(JSONB, default={})

    def __repr__(self) -> str:
        return f"<SystemMetric(id={self.id}, type='{self.metric_type}', name='{self.metric_name}', value={self.value})>"
