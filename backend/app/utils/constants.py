# app/utils/constants.py
"""
상수 정의
"""

from enum import Enum


class UserRole(str, Enum):
    """사용자 역할"""

    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ScenarioStatus(str, Enum):
    """시나리오 상태"""

    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class NodeType(str, Enum):
    """노드 타입"""

    START = "start"
    MESSAGE = "message"
    BRANCH = "branch"
    TRANSFER = "transfer"
    END = "end"
    INPUT = "input"


class GenderType(str, Enum):
    """성별"""

    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class AgeRangeType(str, Enum):
    """연령대"""

    CHILD = "child"
    TWENTIES = "20s"
    THIRTIES = "30s"
    FORTIES = "40s"
    FIFTIES = "50s"
    SENIOR = "senior"


class ModelStatus(str, Enum):
    """모델 상태"""

    TRAINING = "training"
    READY = "ready"
    ERROR = "error"
    DEPRECATED = "deprecated"


class GenerationStatus(str, Enum):
    """TTS 생성 상태"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentEnvironment(str, Enum):
    """배포 환경"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(str, Enum):
    """배포 상태"""

    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class LogLevel(str, Enum):
    """로그 레벨"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# 파일 관련 상수
AUDIO_FILE_EXTENSIONS = [".wav", ".mp3", ".flac", ".ogg"]
MAX_TEXT_LENGTH = 1000
