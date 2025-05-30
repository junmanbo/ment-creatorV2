"""
기본 스키마 클래스
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """기본 스키마 클래스"""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """타임스탬프 믹스인"""
    
    created_at: datetime
    updated_at: datetime


class IDMixin(BaseModel):
    """ID 믹스인"""
    
    id: int


class PaginationSchema(BaseSchema):
    """페이징 스키마"""
    
    page: int
    size: int
    total: int
    pages: int


class ResponseSchema(BaseSchema):
    """기본 응답 스키마"""
    
    success: bool = True
    message: str = "Success"
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None


class ErrorSchema(BaseSchema):
    """에러 스키마"""
    
    code: str
    message: str
    details: Dict[str, Any] = {}


class ErrorResponseSchema(BaseSchema):
    """에러 응답 스키마"""
    
    success: bool = False
    error: ErrorSchema
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None
