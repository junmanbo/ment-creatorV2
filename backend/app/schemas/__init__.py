"""
스키마 모듈 초기화
"""
# 기본 스키마 (먼저 import)
from .base import (
    BaseSchema,
    ErrorResponseSchema,
    ErrorSchema,
    IDMixin,
    PaginationSchema,
    ResponseSchema,
    TimestampMixin,
)

# 공통 스키마
from .common import (
    BulkOperationRequest,
    BulkOperationResponse,
    FileUploadResponse,
    HealthCheckResponse,
    MessageResponse,
    SearchRequest,
    StatsResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)

# 인증 스키마
from .auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenRefreshResponse,
    TokenResponse,
    UserInfo,
)

# 사용자 스키마
from .user import (
    UserChangePassword,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

# 시나리오 스키마
from .scenario import (
    ScenarioConnectionCreate,
    ScenarioConnectionResponse,
    ScenarioConnectionUpdate,
    ScenarioCreate,
    ScenarioDetailResponse,
    ScenarioListResponse,
    ScenarioNodeCreate,
    ScenarioNodeResponse,
    ScenarioNodeUpdate,
    ScenarioResponse,
    ScenarioUpdate,
)

# 성우 스키마
from .voice_actor import (
    VoiceActorCreate,
    VoiceActorListResponse,
    VoiceActorResponse,
    VoiceActorUpdate,
    VoiceModelCreate,
    VoiceModelResponse,
    VoiceModelUpdate,
    VoiceSampleCreate,
    VoiceSampleResponse,
)

# TTS 스키마
from .tts import (
    TTSGenerationListResponse,
    TTSGenerationRequest,
    TTSGenerationResponse,
    TTSLibraryCreate,
    TTSLibraryResponse,
    TTSLibraryUpdate,
    TTSScriptCreate,
    TTSScriptResponse,
    TTSScriptUpdate,
)

__all__ = [
    # Base
    "BaseSchema",
    "IDMixin",
    "TimestampMixin",
    "PaginationSchema",
    "ResponseSchema",
    "ErrorSchema",
    "ErrorResponseSchema",
    
    # Common
    "HealthCheckResponse",
    "MessageResponse",
    "FileUploadResponse",
    "SearchRequest",
    "BulkOperationRequest",
    "BulkOperationResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    "StatsResponse",
    
    # Auth
    "LoginRequest",
    "TokenResponse",
    "TokenRefreshResponse",
    "RefreshTokenRequest",
    "UserInfo",
    
    # User
    "UserCreate",
    "UserUpdate",
    "UserChangePassword",
    "UserResponse",
    "UserListResponse",
    
    # Scenario
    "ScenarioCreate",
    "ScenarioUpdate",
    "ScenarioResponse",
    "ScenarioListResponse",
    "ScenarioDetailResponse",
    "ScenarioNodeCreate",
    "ScenarioNodeUpdate",
    "ScenarioNodeResponse",
    "ScenarioConnectionCreate",
    "ScenarioConnectionUpdate",
    "ScenarioConnectionResponse",
    
    # Voice Actor
    "VoiceActorCreate",
    "VoiceActorUpdate",
    "VoiceActorResponse",
    "VoiceActorListResponse",
    "VoiceModelCreate",
    "VoiceModelUpdate",
    "VoiceModelResponse",
    "VoiceSampleCreate",
    "VoiceSampleResponse",
    
    # TTS
    "TTSScriptCreate",
    "TTSScriptUpdate",
    "TTSScriptResponse",
    "TTSGenerationRequest",
    "TTSGenerationResponse",
    "TTSGenerationListResponse",
    "TTSLibraryCreate",
    "TTSLibraryUpdate",
    "TTSLibraryResponse",
]
