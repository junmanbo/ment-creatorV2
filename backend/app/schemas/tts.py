"""
TTS 관련 스키마
"""
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, PaginationSchema, TimestampMixin
from app.utils.constants import GenerationStatus


class TTSScriptBase(BaseSchema):
    """TTS 스크립트 기본 스키마"""
    
    scenario_id: int
    node_id: str = Field(..., min_length=1, max_length=50)
    text_content: str = Field(..., min_length=1)
    voice_actor_id: Optional[int] = None
    voice_settings: Dict[str, Any] = Field(default_factory=dict)


class TTSScriptCreate(TTSScriptBase):
    """TTS 스크립트 생성 스키마"""
    pass


class TTSScriptUpdate(BaseSchema):
    """TTS 스크립트 수정 스키마"""
    
    text_content: Optional[str] = Field(None, min_length=1)
    voice_actor_id: Optional[int] = None
    voice_settings: Optional[Dict[str, Any]] = None


class TTSScriptResponse(IDMixin, TimestampMixin, TTSScriptBase):
    """TTS 스크립트 응답 스키마"""
    
    created_by: Optional[int] = None


# TTS 생성 스키마
class TTSGenerationRequest(BaseSchema):
    """TTS 생성 요청 스키마"""
    
    voice_model_id: int
    generation_params: Dict[str, Any] = Field(default_factory=dict)


class TTSGenerationBase(BaseSchema):
    """TTS 생성 기본 스키마"""
    
    script_id: int
    voice_model_id: Optional[int] = None
    audio_file_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    quality_score: Optional[float] = None
    status: GenerationStatus = GenerationStatus.PENDING
    error_message: Optional[str] = None
    generation_params: Dict[str, Any] = Field(default_factory=dict)


class TTSGenerationResponse(IDMixin, TimestampMixin, TTSGenerationBase):
    """TTS 생성 응답 스키마"""
    
    requested_by: Optional[int] = None
    started_at: Optional[int] = None
    completed_at: Optional[int] = None


class TTSGenerationListResponse(PaginationSchema):
    """TTS 생성 목록 응답 스키마"""
    
    items: List[TTSGenerationResponse]


# TTS 라이브러리 스키마
class TTSLibraryBase(BaseSchema):
    """TTS 라이브러리 기본 스키마"""
    
    name: str = Field(..., min_length=1, max_length=200)
    text_content: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    voice_actor_id: Optional[int] = None
    audio_file_path: Optional[str] = Field(None, max_length=500)
    is_public: bool = False


class TTSLibraryCreate(TTSLibraryBase):
    """TTS 라이브러리 생성 스키마"""
    pass


class TTSLibraryUpdate(BaseSchema):
    """TTS 라이브러리 수정 스키마"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    text_content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    voice_actor_id: Optional[int] = None
    audio_file_path: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class TTSLibraryResponse(IDMixin, TimestampMixin, TTSLibraryBase):
    """TTS 라이브러리 응답 스키마"""
    
    usage_count: int = 0
    created_by: Optional[int] = None
