from typing import Any


class BaseCustomException(Exception):
    """기본 커스텀 예외 클래스"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(BaseCustomException):
    """인증 오류"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_FAILED",
            status_code=401,
            details=details,
        )


class AuthorizationError(BaseCustomException):
    """권한 오류"""

    def __init__(
        self,
        message: str = "Authorization denied",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_DENIED",
            status_code=403,
            details=details,
        )


class ValidationError(BaseCustomException):
    """검증 오류"""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class NotFoundError(BaseCustomException):
    """리소스 없음 오류"""

    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class DuplicateError(BaseCustomException):
    """중복 리소스 오류"""

    def __init__(
        self,
        message: str = "Duplicate resource",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="DUPLICATE_RESOURCE",
            status_code=409,
            details=details,
        )


class TTSGenerationError(BaseCustomException):
    """TTS 생성 오류"""

    def __init__(
        self,
        message: str = "TTS generation failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="TTS_GENERATION_FAILED",
            status_code=500,
            details=details,
        )


class ModelTrainingError(BaseCustomException):
    """모델 학습 오류"""

    def __init__(
        self,
        message: str = "Model training error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="MODEL_TRAINING_ERROR",
            status_code=500,
            details=details,
        )


class FileUploadError(BaseCustomException):
    """파일 업로드 오류"""

    def __init__(
        self,
        message: str = "File upload error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            status_code=400,
            details=details,
        )


class DeploymentError(BaseCustomException):
    """배포 오류"""

    def __init__(
        self,
        message: str = "Deployment failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="DEPLOYMENT_FAILED",
            status_code=500,
            details=details,
        )


class SimulationError(BaseCustomException):
    """시뮬레이션 오류"""

    def __init__(
        self,
        message: str = "Simulation error",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="SIMULATION_ERROR",
            status_code=500,
            details=details,
        )


class RateLimitError(BaseCustomException):
    """Rate Limit 오류"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )
