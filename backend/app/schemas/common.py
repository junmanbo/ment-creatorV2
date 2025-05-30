"""
공통 스키마
"""
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, PaginationSchema


class HealthCheckResponse(BaseSchema):
    """헬스체크 응답 스키마"""
    
    status: str = "healthy"
    service: str
    version: str
    environment: str


class MessageResponse(BaseSchema):
    """메시지 응답 스키마"""
    
    message: str


class FileUploadResponse(BaseSchema):
    """파일 업로드 응답 스키마"""
    
    filename: str
    file_path: str
    file_size: int
    content_type: Optional[str] = None


class SearchRequest(BaseSchema):
    """검색 요청 스키마"""
    
    query: str = Field(..., min_length=1, max_length=200)
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class BulkOperationRequest(BaseSchema):
    """일괄 작업 요청 스키마"""
    
    ids: List[int] = Field(..., min_items=1)
    action: str = Field(..., min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)


class BulkOperationResponse(BaseSchema):
    """일괄 작업 응답 스키마"""
    
    success_count: int
    failed_count: int
    total_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class ValidationErrorDetail(BaseSchema):
    """검증 오류 상세"""
    
    field: str
    message: str
    value: Any


class ValidationErrorResponse(BaseSchema):
    """검증 오류 응답"""
    
    detail: List[ValidationErrorDetail]


class StatsResponse(BaseSchema):
    """통계 응답 스키마"""
    
    total: int
    active: int
    inactive: int
    today: int
    this_week: int
    this_month: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
