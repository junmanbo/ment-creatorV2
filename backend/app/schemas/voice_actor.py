"""
성우 및 음성 모델 관련 스키마
"""
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, PaginationSchema, TimestampMixin
from app.utils.constants import AgeRangeType, GenderType, ModelStatus


class VoiceActorBase(BaseSchema):
    """성우 기본 스키마"""
    
    name: str = Field(..., min_length=1, max_length=100)
    gender: Optional[GenderType] = None
    age_range: Optional[AgeRangeType] = None
    language: str = Field(default="ko", max_length=10)
    description: Optional[str] = None
    characteristics: Dict[str, Any] = Field(default_factory=dict)
    sample_audio_url: Optional[str] = Field(None, max_length=500)


class VoiceActorCreate(VoiceActorBase):
    """성우 생성 스키마"""
    pass


class VoiceActorUpdate(BaseSchema):
    """성우 수정 스키마"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    gender: Optional[GenderType] = None
    age_range: Optional[AgeRangeType] = None
    language: Optional[str] = Field(None, max_length=10)
    description: Optional[str] = None
    characteristics: Optional[Dict[str, Any]] = None
    sample_audio_url: Optional[str] = Field(None, max_length=500)


class VoiceActorResponse(IDMixin, TimestampMixin, VoiceActorBase):
    """성우 응답 스키마"""
    
    is_active: bool
    created_by: Optional[int] = None


class VoiceActorListResponse(PaginationSchema):
    """성우 목록 응답 스키마"""
    
    items: List[VoiceActorResponse]


# 음성 모델 스키마
class VoiceModelBase(BaseSchema):
    """음성 모델 기본 스키마"""
    
    model_name: str = Field(..., min_length=1, max_length=200)
    model_path: str = Field(..., max_length=500)
    model_version: str = Field(default="1.0", max_length=20)
    training_data_duration: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class VoiceModelCreate(VoiceModelBase):
    """음성 모델 생성 스키마"""
    
    voice_actor_id: int


class VoiceModelUpdate(BaseSchema):
    """음성 모델 수정 스키마"""
    
    model_name: Optional[str] = Field(None, min_length=1, max_length=200)
    model_path: Optional[str] = Field(None, max_length=500)
    model_version: Optional[str] = Field(None, max_length=20)
    training_data_duration: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class VoiceModelResponse(IDMixin, TimestampMixin, VoiceModelBase):
    """음성 모델 응답 스키마"""
    
    voice_actor_id: int
    quality_score: Optional[float] = None
    status: ModelStatus


# 음성 샘플 스키마
class VoiceSampleBase(BaseSchema):
    """음성 샘플 기본 스키마"""
    
    text_content: str = Field(..., min_length=1)
    audio_file_path: str = Field(..., max_length=500)
    duration: Optional[float] = None
    sample_rate: int = 22050
    file_size: Optional[int] = None


class VoiceSampleCreate(BaseSchema):
    """음성 샘플 생성 스키마"""
    
    voice_actor_id: int
    text_content: str = Field(..., min_length=1)


class VoiceSampleResponse(IDMixin, TimestampMixin, VoiceSampleBase):
    """음성 샘플 응답 스키마"""
    
    voice_actor_id: int
    uploaded_by: Optional[int] = None
