# app/models/scenario.py
"""
시나리오 관련 모델
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.constants import NodeType, ScenarioStatus


class Scenario(Base):
    """시나리오 모델"""

    __tablename__ = "scenarios"

    # 기본 정보
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    version = Column(String(20), nullable=False, default="1.0")

    # 상태
    status = Column(Enum(ScenarioStatus), default=ScenarioStatus.DRAFT, nullable=False)
    deployed_at = Column(DateTime)
    is_template = Column(Boolean, default=False, nullable=False)

    # 메타데이터
    metadata = Column(JSONB, default={})

    # 작성자 정보
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))

    # 관계
    creator = relationship(
        "User", foreign_keys=[created_by], back_populates="created_scenarios"
    )
    updater = relationship(
        "User", foreign_keys=[updated_by], back_populates="updated_scenarios"
    )
    nodes = relationship(
        "ScenarioNode", back_populates="scenario", cascade="all, delete-orphan"
    )
    connections = relationship(
        "ScenarioConnection", back_populates="scenario", cascade="all, delete-orphan"
    )
    versions = relationship(
        "ScenarioVersion", back_populates="scenario", cascade="all, delete-orphan"
    )
    tts_scripts = relationship(
        "TTSScript", back_populates="scenario", cascade="all, delete-orphan"
    )
    deployments = relationship("Deployment", back_populates="scenario")

    # 제약 조건
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_scenario_name_version"),
    )

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, name='{self.name}', version='{self.version}', status='{self.status}')>"


class ScenarioNode(Base):
    """시나리오 노드 모델"""

    __tablename__ = "scenario_nodes"

    # 기본 정보
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    node_id = Column(String(50), nullable=False)  # 플로우차트 내 고유 ID
    node_type = Column(Enum(NodeType), nullable=False)
    name = Column(String(200), nullable=False)

    # 위치 정보
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)

    # 설정 정보
    config = Column(JSONB, default={}, nullable=False)

    # 관계
    scenario = relationship("Scenario", back_populates="nodes")
    source_connections = relationship(
        "ScenarioConnection",
        foreign_keys="ScenarioConnection.source_node_id",
        back_populates="source_node",
    )
    target_connections = relationship(
        "ScenarioConnection",
        foreign_keys="ScenarioConnection.target_node_id",
        back_populates="target_node",
    )
    tts_scripts = relationship("TTSScript", back_populates="node")

    # 제약 조건
    __table_args__ = (
        UniqueConstraint("scenario_id", "node_id", name="uq_scenario_node_id"),
    )

    def __repr__(self) -> str:
        return f"<ScenarioNode(id={self.id}, node_id='{self.node_id}', type='{self.node_type}')>"


class ScenarioConnection(Base):
    """시나리오 연결 모델"""

    __tablename__ = "scenario_connections"

    # 기본 정보
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    source_node_id = Column(String(50), nullable=False)
    target_node_id = Column(String(50), nullable=False)

    # 연결 정보
    condition = Column(JSONB)  # 분기 조건
    label = Column(String(100))

    # 관계
    scenario = relationship("Scenario", back_populates="connections")
    source_node = relationship(
        "ScenarioNode",
        foreign_keys=[source_node_id],
        primaryjoin="and_(ScenarioConnection.scenario_id == ScenarioNode.scenario_id, "
        "ScenarioConnection.source_node_id == ScenarioNode.node_id)",
        back_populates="source_connections",
    )
    target_node = relationship(
        "ScenarioNode",
        foreign_keys=[target_node_id],
        primaryjoin="and_(ScenarioConnection.scenario_id == ScenarioNode.scenario_id, "
        "ScenarioConnection.target_node_id == ScenarioNode.node_id)",
        back_populates="target_connections",
    )

    def __repr__(self) -> str:
        return f"<ScenarioConnection(id={self.id}, {self.source_node_id} -> {self.target_node_id})>"


class ScenarioVersion(Base):
    """시나리오 버전 모델"""

    __tablename__ = "scenario_versions"

    # 기본 정보
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    version = Column(String(20), nullable=False)
    snapshot = Column(JSONB, nullable=False)  # 전체 시나리오 스냅샷
    notes = Column(Text)

    # 작성자 정보
    created_by = Column(Integer, ForeignKey("users.id"))

    # 관계
    scenario = relationship("Scenario", back_populates="versions")
    creator = relationship("User")

    # 제약 조건
    __table_args__ = (
        UniqueConstraint("scenario_id", "version", name="uq_scenario_version"),
    )

    def __repr__(self) -> str:
        return f"<ScenarioVersion(id={self.id}, scenario_id={self.scenario_id}, version='{self.version}')>"
