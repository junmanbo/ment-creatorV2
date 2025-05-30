# app/api/v1/endpoints/monitoring.py
"""
모니터링 관련 엔드포인트
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_manager_user
from app.api.dependencies.database import get_async_session
from app.models.user import User
from app.schemas.monitoring import (
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    SystemMetricResponse,
    DashboardResponse,
)
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """대시보드 데이터 조회"""
    monitoring_service = MonitoringService()
    dashboard_data = await monitoring_service.get_dashboard_data(db)
    return DashboardResponse(**dashboard_data)


@router.get("/metrics/system", response_model=List[SystemMetricResponse])
async def get_system_metrics(
    metric_type: Optional[str] = Query(None, description="메트릭 타입"),
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간"),
    interval: Optional[str] = Query("1h", description="집계 간격"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시스템 메트릭 조회"""
    monitoring_service = MonitoringService()
    
    # 기본값 설정
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    metrics = await monitoring_service.get_system_metrics(
        db,
        metric_type=metric_type,
        start_time=start_time,
        end_time=end_time,
        interval=interval
    )
    
    return [SystemMetricResponse.model_validate(metric) for metric in metrics]


@router.get("/metrics/tts")
async def get_tts_metrics(
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 생성 메트릭 조회"""
    monitoring_service = MonitoringService()
    
    # 기본값 설정
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    metrics = await monitoring_service.get_tts_metrics(
        db,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "total_generations": metrics["total_count"],
        "completed_generations": metrics["completed_count"],
        "failed_generations": metrics["failed_count"],
        "average_generation_time": metrics["avg_generation_time"],
        "success_rate": metrics["success_rate"],
        "daily_breakdown": metrics["daily_breakdown"],
        "voice_actor_breakdown": metrics["voice_actor_breakdown"]
    }


@router.get("/metrics/scenarios")
async def get_scenario_metrics(
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시나리오 사용 메트릭 조회"""
    monitoring_service = MonitoringService()
    
    # 기본값 설정
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)
    
    metrics = await monitoring_service.get_scenario_metrics(
        db,
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "active_scenarios": metrics["active_count"],
        "total_scenarios": metrics["total_count"],
        "most_used_scenarios": metrics["top_scenarios"],
        "deployment_frequency": metrics["deployment_stats"],
        "status_breakdown": metrics["status_breakdown"]
    }


@router.get("/health")
async def get_health_status(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시스템 헬스 체크"""
    monitoring_service = MonitoringService()
    health_status = await monitoring_service.get_health_status(db)
    
    return {
        "overall_status": health_status["status"],
        "services": health_status["services"],
        "database": health_status["database"],
        "storage": health_status["storage"],
        "memory_usage": health_status["memory_usage"],
        "cpu_usage": health_status["cpu_usage"],
        "disk_usage": health_status["disk_usage"],
        "timestamp": datetime.utcnow()
    }


@router.get("/alerts", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)
):
    """알림 규칙 목록 조회"""
    monitoring_service = MonitoringService()
    rules = await monitoring_service.get_alert_rules(db)
    return [AlertRuleResponse.model_validate(rule) for rule in rules]


@router.post("/alerts/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_in: AlertRuleCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_manager_user)
):
    """알림 규칙 생성"""
    monitoring_service = MonitoringService()
    rule = await monitoring_service.create_alert_rule(
        db,
        rule_in=rule_in,
        created_by=current_user.id
    )
    return AlertRuleResponse.model_validate(rule)


@router.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_in: AlertRuleUpdate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)
):
    """알림 규칙 수정"""
    monitoring_service = MonitoringService()
    rule = await monitoring_service.get_or_404(db, rule_id)
    updated_rule = await monitoring_service.update(
        db,
        db_obj=rule,
        obj_in=rule_in.model_dump(exclude_unset=True)
    )
    return AlertRuleResponse.model_validate(updated_rule)


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)
):
    """알림 규칙 삭제"""
    monitoring_service = MonitoringService()
    await monitoring_service.delete(db, id=rule_id)
    return {"message": "Alert rule deleted successfully"}


@router.get("/logs/audit")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="사용자 ID 필터"),
    action: Optional[str] = Query(None, description="액션 필터"),
    resource_type: Optional[str] = Query(None, description="리소스 타입 필터"),
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간"),
    limit: int = Query(100, description="조회 개수"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)
):
    """감사 로그 조회"""
    monitoring_service = MonitoringService()
    
    # 기본값 설정
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    logs = await monitoring_service.get_audit_logs(
        db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return {
        "logs": logs,
        "total": len(logs),
        "filters": {
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "start_time": start_time,
            "end_time": end_time
        }
    }


@router.get("/logs/system")
async def get_system_logs(
    level: Optional[str] = Query(None, description="로그 레벨 필터"),
    module: Optional[str] = Query(None, description="모듈 필터"),
    start_time: Optional[datetime] = Query(None, description="시작 시간"),
    end_time: Optional[datetime] = Query(None, description="종료 시간"),
    limit: int = Query(100, description="조회 개수"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_manager_user)
):
    """시스템 로그 조회"""
    monitoring_service = MonitoringService()
    
    # 기본값 설정
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(hours=24)
    
    logs = await monitoring_service.get_system_logs(
        db,
        level=level,
        module=module,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return {
        "logs": logs,
        "total": len(logs),
        "filters": {
            "level": level,
            "module": module,
            "start_time": start_time,
            "end_time": end_time
        }
    }
