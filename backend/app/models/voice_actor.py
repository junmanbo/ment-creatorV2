"""
성우 및 음성 모델 관련 모델
"""

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.utils.constants import AgeRangeType, GenderType, ModelStatus


class VoiceActor(Base):
    """성우 모델"""

    __tablename__ = "voice_actors"

    # 기본 정보
    name = Column(String(100), nullable=False)
    gender = Column(Enum(GenderType))
    age_range = Column(Enum(AgeRangeType))
    language = Column(String(10), default="ko", nullable=False)
    description = Column(Text)

    # 음성 특징
    characteristics = Column(JSONB, default={})  # 톤, 스타일 등
    sample_audio_url = Column(String(500))

    # 상태
    is_active = Column(Boolean, default=True, nullable=False)

    # 작성자 정보
    created_by = Column(Integer, ForeignKey("users.id"))

    # 관계 (단순한 관계만)
    creator = relationship("User")

    def __repr__(self) -> str:
        return f"<VoiceActor(id={self.id}, name='{self.name}', gender='{self.gender}')>"


class VoiceModel(Base):
    """음성 모델"""

    __tablename__ = "voice_models"

    # 기본 정보
    voice_actor_id = Column(Integer, ForeignKey("voice_actors.id"), nullable=False)
    model_name = Column(String(200), nullable=False)
    model_path = Column(String(500), nullable=False)
    model_version = Column(String(20), default="1.0", nullable=False)

    # 학습 정보
    training_data_duration = Column(Integer)  # 학습 데이터 시간(초)
    quality_score = Column(Float)
    status = Column(Enum(ModelStatus), default=ModelStatus.TRAINING, nullable=False)

    # 설정 정보
    config = Column(JSONB, default={})

    # 관계 (단순한 관계만)
    voice_actor = relationship("VoiceActor")

    def __repr__(self) -> str:
        return f"<VoiceModel(id={self.id}, name='{self.model_name}', status='{self.status}')>"


class VoiceSample(Base):
    """음성 샘플"""

    __tablename__ = "voice_samples"

    # 기본 정보
    voice_actor_id = Column(Integer, ForeignKey("voice_actors.id"), nullable=False)
    text_content = Column(Text, nullable=False)
    audio_file_path = Column(String(500), nullable=False)

    # 오디오 정보
    duration = Column(Float)  # 초 단위
    sample_rate = Column(Integer, default=22050)
    file_size = Column(Integer)  # bytes

    # 업로드 정보
    uploaded_by = Column(Integer, ForeignKey("users.id"))

    # 관계 (단순한 관계만)
    voice_actor = relationship("VoiceActor")
    uploader = relationship("User")

    def __repr__(self) -> str:
        return f"<VoiceSample(id={self.id}, voice_actor_id={self.voice_actor_id}, duration={self.duration})>"
