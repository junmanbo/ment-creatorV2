"""
TTS 관련 모델
"""

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base
from app.utils.constants import GenerationStatus


class TTSScript(Base):
    """TTS 스크립트"""

    __tablename__ = "tts_scripts"

    # 기본 정보
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    node_id = Column(String(50), nullable=False)
    text_content = Column(Text, nullable=False)

    # 음성 설정
    voice_actor_id = Column(Integer, ForeignKey("voice_actors.id"))
    voice_settings = Column(JSONB, default={})  # 속도, 톤, 감정 설정

    # 작성자 정보
    created_by = Column(Integer, ForeignKey("users.id"))

    # 관계 제거 (임시)
    # scenario = relationship("Scenario")
    # voice_actor = relationship("VoiceActor")
    # creator = relationship("User")

    def __repr__(self) -> str:
        return f"<TTSScript(id={self.id}, scenario_id={self.scenario_id}, node_id='{self.node_id}')>"


class TTSGeneration(Base):
    """TTS 생성"""

    __tablename__ = "tts_generations"

    # 기본 정보
    script_id = Column(Integer, ForeignKey("tts_scripts.id"), nullable=False)
    voice_model_id = Column(Integer, ForeignKey("voice_models.id"))

    # 생성 결과
    audio_file_path = Column(String(500))
    file_size = Column(Integer)  # bytes
    duration = Column(Float)  # 초 단위
    quality_score = Column(Float)

    # 상태 정보
    status = Column(
        Enum(GenerationStatus), default=GenerationStatus.PENDING, nullable=False
    )
    error_message = Column(Text)

    # 생성 설정
    generation_params = Column(JSONB, default={})

    # 요청 정보
    requested_by = Column(Integer, ForeignKey("users.id"))
    started_at = Column(Integer)  # Unix timestamp
    completed_at = Column(Integer)  # Unix timestamp

    # 관계 제거 (임시)
    # script = relationship("TTSScript")
    # voice_model = relationship("VoiceModel")
    # requester = relationship("User")

    def __repr__(self) -> str:
        return f"<TTSGeneration(id={self.id}, script_id={self.script_id}, status='{self.status}')>"


class TTSLibrary(Base):
    """TTS 라이브러리"""

    __tablename__ = "tts_library"

    # 기본 정보
    name = Column(String(200), nullable=False)
    text_content = Column(Text, nullable=False)
    category = Column(String(100))
    tags = Column(String(500))  # 쉼표로 구분된 태그

    # 음성 정보
    voice_actor_id = Column(Integer, ForeignKey("voice_actors.id"))
    audio_file_path = Column(String(500))

    # 사용 통계
    usage_count = Column(Integer, default=0, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)

    # 작성자 정보
    created_by = Column(Integer, ForeignKey("users.id"))

    # 관계 제거 (임시)
    # voice_actor = relationship("VoiceActor")
    # creator = relationship("User")

    def __repr__(self) -> str:
        return f"<TTSLibrary(id={self.id}, name='{self.name}', category='{self.category}')>"
