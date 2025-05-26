# app/models/user.py
"""
사용자 모델
"""

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.constants import UserRole


class User(Base):
    """사용자 모델"""

    __tablename__ = "users"

    # 기본 정보
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)

    # 역할 및 권한
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    department = Column(String(100))
    phone = Column(String(20))

    # 상태
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime)

    # 관계
    created_scenarios = relationship(
        "Scenario", foreign_keys="Scenario.created_by", back_populates="creator"
    )
    updated_scenarios = relationship(
        "Scenario", foreign_keys="Scenario.updated_by", back_populates="updater"
    )
    voice_actors = relationship("VoiceActor", back_populates="creator")
    tts_scripts = relationship("TTSScript", back_populates="creator")
    tts_generations = relationship("TTSGeneration", back_populates="requester")
    deployments = relationship("Deployment", back_populates="deployer")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
