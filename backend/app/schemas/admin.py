# app/schemas/admin.py
"""
관리자 관련 스키마
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SystemSettingsResponse(BaseModel):
    """시스템 설정 응답"""
    project_name: str = Field(..., description="프로젝트 이름")
    version: str = Field(..., description="버전")
    environment: str = Field(..., description="환경")
    debug: bool = Field(..., description="디버그 모드")
    max_file_size: int = Field(..., description="최대 파일 크기")
    allowed_file_extensions: List[str] = Field(..., description="허용된 파일 확장자")
    default_page_size: int = Field(..., description="기본 페이지 크기")
    max_page_size: int = Field(..., description="최대 페이지 크기")
    tts_max_text_length: int = Field(..., description="TTS 최대 텍스트 길이")
    tts_generation_timeout: int = Field(..., description="TTS 생성 타임아웃")
    rate_limits: Dict[str, str] = Field(..., description="Rate Limit 설정")


class SystemSettingsUpdate(BaseModel):
    """시스템 설정 업데이트"""
    max_file_size: Optional[int] = Field(None, description="최대 파일 크기")
    allowed_file_extensions: Optional[List[str]] = Field(None, description="허용된 파일 확장자")
    default_page_size: Optional[int] = Field(None, description="기본 페이지 크기")
    max_page_size: Optional[int] = Field(None, description="최대 페이지 크기")
    tts_max_text_length: Optional[int] = Field(None, description="TTS 최대 텍스트 길이")
    tts_generation_timeout: Optional[int] = Field(None, description="TTS 생성 타임아웃")
    rate_limits: Optional[Dict[str, str]] = Field(None, description="Rate Limit 설정")


class SystemOverview(BaseModel):
    """시스템 개요"""
    total_users: int = Field(..., description="총 사용자 수")
    active_users: int = Field(..., description="활성 사용자 수")
    total_scenarios: int = Field(..., description="총 시나리오 수")
    active_scenarios: int = Field(..., description="활성 시나리오 수")
    total_voice_actors: int = Field(..., description="총 성우 수")
    tts_generations_today: int = Field(..., description="오늘 TTS 생성 수")
    tts_generations_total: int = Field(..., description="총 TTS 생성 수")
    storage_usage: Dict[str, Any] = Field(..., description="저장소 사용량")
    system_health: str = Field(..., description="시스템 상태")
    uptime: float = Field(..., description="가동 시간")


class DatabaseStatus(BaseModel):
    """데이터베이스 상태"""
    connection_count: int = Field(..., description="연결 수")
    active_queries: int = Field(..., description="활성 쿼리 수")
    database_size: str = Field(..., description="데이터베이스 크기")
    table_sizes: List[Dict[str, Any]] = Field(..., description="테이블 크기들")
    index_usage: List[Dict[str, Any]] = Field(default_factory=list, description="인덱스 사용량")
    slow_queries: List[Dict[str, Any]] = Field(default_factory=list, description="느린 쿼리들")


class DatabaseOptimizationResult(BaseModel):
    """데이터베이스 최적화 결과"""
    analyze_only: bool = Field(..., description="분석만 수행 여부")
    optimization_performed: bool = Field(..., description="최적화 수행 여부")
    tables_optimized: List[str] = Field(..., description="최적화된 테이블들")
    space_freed: int = Field(..., description="확보된 공간 (bytes)")
    performance_improvement: str = Field(..., description="성능 개선 정보")


class BackupCreateRequest(BaseModel):
    """백업 생성 요청"""
    backup_type: str = Field(default="full", description="백업 타입 (full, database, files)")
    include_files: bool = Field(default=True, description="파일 포함 여부")
    compression: bool = Field(default=True, description="압축 여부")


class BackupResponse(BaseModel):
    """백업 응답"""
    id: int = Field(..., description="백업 ID")
    name: str = Field(..., description="백업 이름")
    backup_type: str = Field(..., description="백업 타입")
    path: str = Field(..., description="백업 경로")
    size: int = Field(..., description="백업 크기 (bytes)")
    compressed: bool = Field(..., description="압축 여부")
    created_by: Optional[int] = Field(None, description="생성자 ID")
    created_at: datetime = Field(..., description="생성일시")

    class Config:
        from_attributes = True


class BackupRestoreResult(BaseModel):
    """백업 복원 결과"""
    backup_id: int = Field(..., description="백업 ID")
    restore_status: str = Field(..., description="복원 상태")
    restored_tables: List[str] = Field(..., description="복원된 테이블들")
    restored_files: List[str] = Field(..., description="복원된 파일들")
    restore_time: int = Field(..., description="복원 시간 (초)")


class MaintenanceRequest(BaseModel):
    """유지보수 모드 요청"""
    enabled: bool = Field(..., description="유지보수 모드 활성화")
    message: Optional[str] = Field(None, description="유지보수 메시지")
    estimated_duration: Optional[int] = Field(None, description="예상 시간 (분)")


class MaintenanceStatus(BaseModel):
    """유지보수 모드 상태"""
    maintenance_mode: bool = Field(..., description="유지보수 모드 여부")
    message: Optional[str] = Field(None, description="유지보수 메시지")
    estimated_duration: Optional[int] = Field(None, description="예상 시간 (분)")
    set_at: Optional[datetime] = Field(None, description="설정일시")
    set_by: Optional[int] = Field(None, description="설정자 ID")


class CacheClearResult(BaseModel):
    """캐시 정리 결과"""
    cache_type: str = Field(..., description="캐시 타입")
    cleared_items: int = Field(..., description="정리된 항목 수")
    size_freed: int = Field(..., description="확보된 크기 (bytes)")
    time_taken: float = Field(..., description="소요 시간 (초)")


class CleanupTaskResult(BaseModel):
    """정리 작업 결과"""
    task_type: str = Field(..., description="작업 타입")
    dry_run: bool = Field(..., description="미리보기 모드")
    results: Dict[str, Any] = Field(..., description="작업 결과들")
    total_cleaned: int = Field(..., description="총 정리된 항목 수")
    size_freed: int = Field(..., description="확보된 크기 (bytes)")


class ImpersonationTokenResponse(BaseModel):
    """사용자 대신 로그인 토큰 응답"""
    impersonation_token: str = Field(..., description="대신 로그인 토큰")
    target_user_id: int = Field(..., description="대상 사용자 ID")
    expires_at: datetime = Field(..., description="만료일시")
    admin_user: str = Field(..., description="관리자 사용자명")


class DetailedHealthStatus(BaseModel):
    """상세 헬스 상태"""
    overall_status: str = Field(..., description="전체 상태")
    components: Dict[str, Dict[str, Any]] = Field(..., description="컴포넌트들")
    performance: Dict[str, Any] = Field(..., description="성능 메트릭")
    alerts: List[str] = Field(default_factory=list, description="알림들")
    recommendations: List[str] = Field(default_factory=list, description="권장사항들")


class SystemStatsDetailed(BaseModel):
    """상세 시스템 통계"""
    user_activity: Dict[str, Any] = Field(..., description="사용자 활동")
    tts_usage: Dict[str, Any] = Field(..., description="TTS 사용량")
    scenario_usage: Dict[str, Any] = Field(..., description="시나리오 사용량")
    error_rates: Dict[str, Any] = Field(..., description="에러율")
    performance_metrics: Dict[str, Any] = Field(..., description="성능 메트릭")
    resource_usage: Dict[str, Any] = Field(..., description="리소스 사용량")


class SystemLogEntry(BaseModel):
    """시스템 로그 엔트리"""
    id: int = Field(..., description="로그 ID")
    level: str = Field(..., description="로그 레벨")
    message: str = Field(..., description="로그 메시지")
    module: Optional[str] = Field(None, description="모듈")
    created_at: datetime = Field(..., description="생성일시")


class AuditLogEntry(BaseModel):
    """감사 로그 엔트리"""
    id: int = Field(..., description="로그 ID")
    user_id: Optional[int] = Field(None, description="사용자 ID")
    action: str = Field(..., description="액션")
    resource_type: str = Field(..., description="리소스 타입")
    created_at: datetime = Field(..., description="생성일시")


class EnvironmentStatus(BaseModel):
    """환경 상태"""
    environment: str = Field(..., description="환경")
    active_deployments: int = Field(..., description="활성 배포 수")
    pending_deployments: int = Field(..., description="대기 중인 배포 수")
    last_deployment: Optional[datetime] = Field(None, description="마지막 배포일시")
    health_status: str = Field(..., description="헬스 상태")
