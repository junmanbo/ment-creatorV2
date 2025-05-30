# app/schemas/monitoring.py
"""
모니터링 스키마
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema, IDMixin, TimestampSchema


class SystemMetricBase(BaseSchema):
    """시스템 메트릭 기본 스키마"""

    metric_type: str = Field(..., description="메트릭 타입")
    metric_name: str = Field(..., description="메트릭 이름")
    value: float = Field(..., description="메트릭 값")
    unit: str | None = Field(None, description="단위")
    tags: dict[str, Any] | None = Field(default_factory=dict, description="태그")


class SystemMetricCreate(SystemMetricBase):
    """시스템 메트릭 생성 스키마"""

    pass


class SystemMetricResponse(SystemMetricBase, IDMixin, TimestampSchema):
    """시스템 메트릭 응답 스키마"""

    class Config:
        from_attributes = True


class MetricsQueryParams(BaseSchema):
    """메트릭 조회 파라미터"""

    metric_type: str | None = Field(None, description="메트릭 타입 필터")
    start_time: str | None = Field(None, description="시작 시간 (ISO format)")
    end_time: str | None = Field(None, description="종료 시간 (ISO format)")
    interval: str | None = Field("1h", description="집계 간격 (1m, 5m, 1h, 1d)")


class DashboardMetrics(BaseSchema):
    """대시보드 메트릭"""

    active_scenarios: int
    tts_generations_pending: int
    tts_generations_completed: int
    voice_models_count: int
    system_status: str


class AlertRuleBase(BaseModel):
    """알림 규칙 기본 스키마"""
    name: str = Field(..., description="규칙 이름")
    metric_type: str = Field(..., description="메트릭 타입")
    condition: str = Field(..., description="조건 (>, <, ==, etc.)")
    threshold: float = Field(..., description="임계값")
    enabled: bool = Field(default=True, description="활성화 여부")
    description: Optional[str] = Field(None, description="설명")


class AlertRuleCreate(AlertRuleBase):
    """알림 규칙 생성 스키마"""
    pass


class AlertRuleUpdate(BaseModel):
    """알림 규칙 수정 스키마"""
    name: Optional[str] = Field(None, description="규칙 이름")
    condition: Optional[str] = Field(None, description="조건")
    threshold: Optional[float] = Field(None, description="임계값")
    enabled: Optional[bool] = Field(None, description="활성화 여부")
    description: Optional[str] = Field(None, description="설명")


class AlertRuleResponse(AlertRuleBase):
    """알림 규칙 응답 스키마"""
    id: int = Field(..., description="규칙 ID")
    created_by: Optional[int] = Field(None, description="생성자 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """대시보드 응답 스키마"""
    statistics: Dict[str, Any] = Field(..., description="기본 통계")
    system_health: Dict[str, Any] = Field(..., description="시스템 상태")
    timestamp: datetime = Field(..., description="조회 시간")


class HealthStatusResponse(BaseModel):
    """헬스 상태 응답 스키마"""
    overall_status: str = Field(..., description="전체 상태")
    services: Dict[str, str] = Field(..., description="서비스별 상태")
    database: Dict[str, Any] = Field(..., description="데이터베이스 상태")
    storage: Dict[str, Any] = Field(..., description="저장소 상태")
    memory_usage: float = Field(..., description="메모리 사용률")
    cpu_usage: float = Field(..., description="CPU 사용률")
    disk_usage: float = Field(..., description="디스크 사용률")
    timestamp: datetime = Field(..., description="조회 시간")


class TTSMetricsResponse(BaseModel):
    """TTS 메트릭 응답 스키마"""
    total_generations: int = Field(..., description="총 생성 수")
    completed_generations: int = Field(..., description="완료된 생성 수")
    failed_generations: int = Field(..., description="실패한 생성 수")
    average_generation_time: float = Field(..., description="평균 생성 시간")
    success_rate: float = Field(..., description="성공률 (%)")
    daily_breakdown: List[Dict[str, Any]] = Field(..., description="일별 분석")
    voice_actor_breakdown: List[Dict[str, Any]] = Field(..., description="성우별 분석")


class ScenarioMetricsResponse(BaseModel):
    """시나리오 메트릭 응답 스키마"""
    active_scenarios: int = Field(..., description="활성 시나리오 수")
    total_scenarios: int = Field(..., description="총 시나리오 수")
    most_used_scenarios: List[Dict[str, Any]] = Field(..., description="가장 많이 사용된 시나리오들")
    deployment_frequency: Dict[str, Any] = Field(..., description="배포 빈도")
    status_breakdown: List[Dict[str, Any]] = Field(..., description="상태별 분석")


class AuditLogResponse(BaseModel):
    """감사 로그 응답 스키마"""
    logs: List[Dict[str, Any]] = Field(..., description="로그 목록")
    total: int = Field(..., description="총 개수")
    filters: Dict[str, Any] = Field(..., description="적용된 필터")


class SystemLogResponse(BaseModel):
    """시스템 로그 응답 스키마"""
    logs: List[Dict[str, Any]] = Field(..., description="로그 목록")
    total: int = Field(..., description="총 개수")
    filters: Dict[str, Any] = Field(..., description="적용된 필터")


class PerformanceMetrics(BaseModel):
    """성능 메트릭 스키마"""
    response_time: float = Field(..., description="평균 응답 시간 (ms)")
    throughput: float = Field(..., description="처리량 (requests/sec)")
    error_rate: float = Field(..., description="에러율 (%)")
    memory_usage: float = Field(..., description="메모리 사용률 (%)")
    cpu_usage: float = Field(..., description="CPU 사용률 (%)")
    timestamp: datetime = Field(..., description="측정 시간")
