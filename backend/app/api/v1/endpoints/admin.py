# app/api/v1/endpoints/admin.py
"""
관리자 전용 엔드포인트
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_admin_user
from app.api.dependencies.database import get_async_session
from app.models.user import User
from app.schemas.admin import (
    SystemSettingsResponse,
    SystemSettingsUpdate,
    BackupCreateRequest,
    BackupResponse,
    MaintenanceRequest,
)
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/settings", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """시스템 설정 조회"""
    admin_service = AdminService()
    settings = await admin_service.get_system_settings(db)
    return SystemSettingsResponse(**settings)


@router.put("/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_admin_user)
):
    """시스템 설정 변경"""
    admin_service = AdminService()
    updated_settings = await admin_service.update_system_settings(
        db,
        settings_update=settings_update,
        updated_by=current_user.id
    )
    return SystemSettingsResponse(**updated_settings)


@router.get("/stats/overview")
async def get_system_overview(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """시스템 개요 통계"""
    admin_service = AdminService()
    overview = await admin_service.get_system_overview(db)
    return {
        "total_users": overview["user_count"],
        "active_users": overview["active_user_count"],
        "total_scenarios": overview["scenario_count"],
        "active_scenarios": overview["active_scenario_count"],
        "total_voice_actors": overview["voice_actor_count"],
        "tts_generations_today": overview["tts_today"],
        "tts_generations_total": overview["tts_total"],
        "storage_usage": overview["storage_usage"],
        "system_health": overview["health_status"],
        "uptime": overview["uptime"]
    }


@router.get("/stats/detailed")
async def get_detailed_stats(
    days: int = Query(30, description="조회 기간 (일)"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """상세 시스템 통계"""
    admin_service = AdminService()
    stats = await admin_service.get_detailed_stats(db, days=days)
    return {
        "user_activity": stats["user_activity"],
        "tts_usage": stats["tts_usage"],
        "scenario_usage": stats["scenario_usage"],
        "error_rates": stats["error_rates"],
        "performance_metrics": stats["performance_metrics"],
        "resource_usage": stats["resource_usage"]
    }


@router.get("/database/status")
async def get_database_status(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """데이터베이스 상태 조회"""
    admin_service = AdminService()
    db_status = await admin_service.get_database_status(db)
    return {
        "connection_count": db_status["connections"],
        "active_queries": db_status["active_queries"],
        "database_size": db_status["size"],
        "table_sizes": db_status["table_sizes"],
        "index_usage": db_status["index_usage"],
        "slow_queries": db_status["slow_queries"]
    }


@router.post("/database/optimize")
async def optimize_database(
    analyze_only: bool = Query(False, description="분석만 수행"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """데이터베이스 최적화"""
    admin_service = AdminService()
    result = await admin_service.optimize_database(db, analyze_only=analyze_only)
    return {
        "analyze_only": analyze_only,
        "optimization_performed": result["performed"],
        "tables_optimized": result["tables"],
        "space_freed": result["space_freed"],
        "performance_improvement": result["improvement"]
    }


@router.post("/backup", response_model=BackupResponse)
async def create_backup(
    backup_request: BackupCreateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_admin_user)
):
    """시스템 백업 생성"""
    admin_service = AdminService()
    backup = await admin_service.create_backup(
        db,
        backup_type=backup_request.backup_type,
        include_files=backup_request.include_files,
        compression=backup_request.compression,
        created_by=current_user.id
    )
    return BackupResponse.model_validate(backup)


@router.get("/backups", response_model=List[BackupResponse])
async def get_backups(
    limit: int = Query(20, description="조회 개수"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """백업 목록 조회"""
    admin_service = AdminService()
    backups = await admin_service.get_backups(db, limit=limit)
    return [BackupResponse.model_validate(backup) for backup in backups]


@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: int,
    confirm: bool = Query(False, description="복원 확인"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_admin_user)
):
    """백업 복원"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="복원을 진행하려면 confirm=true로 설정하세요."
        )
    
    admin_service = AdminService()
    result = await admin_service.restore_backup(
        db,
        backup_id=backup_id,
        restored_by=current_user.id
    )
    return {
        "backup_id": backup_id,
        "restore_status": result["status"],
        "restored_tables": result["tables"],
        "restored_files": result["files"],
        "restore_time": result["time"]
    }


@router.delete("/backups/{backup_id}")
async def delete_backup(
    backup_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """백업 삭제"""
    admin_service = AdminService()
    await admin_service.delete_backup(db, backup_id)
    return {"message": "백업이 삭제되었습니다."}


@router.post("/maintenance")
async def set_maintenance_mode(
    maintenance_request: MaintenanceRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_admin_user)
):
    """유지보수 모드 설정"""
    admin_service = AdminService()
    result = await admin_service.set_maintenance_mode(
        db,
        enabled=maintenance_request.enabled,
        message=maintenance_request.message,
        estimated_duration=maintenance_request.estimated_duration,
        set_by=current_user.id
    )
    return {
        "maintenance_mode": result["enabled"],
        "message": result["message"],
        "estimated_duration": result["duration"],
        "set_at": result["set_at"]
    }


@router.get("/maintenance")
async def get_maintenance_status(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """유지보수 모드 상태 조회"""
    admin_service = AdminService()
    status = await admin_service.get_maintenance_status(db)
    return {
        "maintenance_mode": status["enabled"],
        "message": status["message"],
        "estimated_duration": status["duration"],
        "set_at": status["set_at"],
        "set_by": status["set_by"]
    }


@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = Query(None, description="캐시 타입 (all, redis, file)"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """캐시 정리"""
    admin_service = AdminService()
    result = await admin_service.clear_cache(db, cache_type=cache_type)
    return {
        "cache_type": cache_type or "all",
        "cleared_items": result["items"],
        "size_freed": result["size"],
        "time_taken": result["time"]
    }


@router.get("/logs/system", response_model=List[Dict])
async def get_system_logs(
    level: Optional[str] = Query(None, description="로그 레벨"),
    limit: int = Query(100, description="조회 개수"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """시스템 로그 조회"""
    admin_service = AdminService()
    logs = await admin_service.get_system_logs(
        db,
        level=level,
        limit=limit
    )
    return logs


@router.get("/logs/audit", response_model=List[Dict])
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="사용자 ID"),
    action: Optional[str] = Query(None, description="액션"),
    limit: int = Query(100, description="조회 개수"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """감사 로그 조회"""
    admin_service = AdminService()
    logs = await admin_service.get_audit_logs(
        db,
        user_id=user_id,
        action=action,
        limit=limit
    )
    return logs


@router.post("/tasks/cleanup")
async def run_cleanup_tasks(
    task_type: str = Query("all", description="정리 작업 타입"),
    dry_run: bool = Query(False, description="미리보기 모드"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """정리 작업 실행"""
    admin_service = AdminService()
    result = await admin_service.run_cleanup_tasks(
        db,
        task_type=task_type,
        dry_run=dry_run
    )
    return {
        "task_type": task_type,
        "dry_run": dry_run,
        "results": result["results"],
        "total_cleaned": result["total"],
        "size_freed": result["size_freed"]
    }


@router.post("/users/{user_id}/impersonate")
async def impersonate_user(
    user_id: int,
    duration_minutes: int = Query(60, description="세션 지속 시간 (분)"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_admin_user)
):
    """사용자 대신 로그인 (개발/디버깅용)"""
    admin_service = AdminService()
    impersonation_token = await admin_service.create_impersonation_token(
        db,
        target_user_id=user_id,
        admin_user_id=current_user.id,
        duration_minutes=duration_minutes
    )
    return {
        "impersonation_token": impersonation_token["token"],
        "target_user_id": user_id,
        "expires_at": impersonation_token["expires_at"],
        "admin_user": current_user.username
    }


@router.get("/health/detailed")
async def get_detailed_health(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_admin_user)
):
    """상세 헬스 체크"""
    admin_service = AdminService()
    health = await admin_service.get_detailed_health(db)
    return {
        "overall_status": health["status"],
        "components": health["components"],
        "performance": health["performance"],
        "alerts": health["alerts"],
        "recommendations": health["recommendations"]
    }
