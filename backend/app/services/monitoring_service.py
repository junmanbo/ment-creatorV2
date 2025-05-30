# app/services/monitoring_service.py
"""
모니터링 서비스
"""
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.audit import AuditLog, SystemLog
from app.models.monitoring import SystemMetric
from app.models.scenario import Scenario
from app.models.tts import TTSGeneration
from app.models.user import User
from app.models.voice_actor import VoiceActor
from app.services.base import BaseService
from app.utils.constants import GenerationStatus, ScenarioStatus
from app.utils.logger import logger


class MonitoringService(BaseService):
    """모니터링 서비스"""

    def __init__(self):
        super().__init__(SystemMetric)

    async def get_dashboard_data(self, db: AsyncSession) -> Dict:
        """대시보드 데이터 조회"""
        # 기본 통계
        user_count = await self._get_count(db, User)
        active_user_count = await self._get_count(db, User, User.is_active == True)
        scenario_count = await self._get_count(db, Scenario)
        active_scenario_count = await self._get_count(db, Scenario, Scenario.status == ScenarioStatus.ACTIVE)
        voice_actor_count = await self._get_count(db, VoiceActor)
        
        # TTS 생성 통계 (오늘)
        today = datetime.utcnow().date()
        tts_today = await self._get_count(
            db, TTSGeneration,
            func.date(TTSGeneration.created_at) == today
        )
        
        tts_completed_today = await self._get_count(
            db, TTSGeneration,
            and_(
                func.date(TTSGeneration.created_at) == today,
                TTSGeneration.status == GenerationStatus.COMPLETED
            )
        )
        
        # 시스템 상태
        system_health = await self._get_system_health()
        
        return {
            "statistics": {
                "total_users": user_count,
                "active_users": active_user_count,
                "total_scenarios": scenario_count,
                "active_scenarios": active_scenario_count,
                "total_voice_actors": voice_actor_count,
                "tts_today": tts_today,
                "tts_completed_today": tts_completed_today
            },
            "system_health": system_health,
            "timestamp": datetime.utcnow()
        }

    async def get_system_metrics(
        self,
        db: AsyncSession,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: str = "1h"
    ) -> List[SystemMetric]:
        """시스템 메트릭 조회"""
        query = select(SystemMetric)
        
        if metric_type:
            query = query.where(SystemMetric.metric_type == metric_type)
        
        if start_time:
            query = query.where(SystemMetric.created_at >= start_time)
        
        if end_time:
            query = query.where(SystemMetric.created_at <= end_time)
        
        query = query.order_by(SystemMetric.created_at.desc()).limit(1000)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_tts_metrics(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """TTS 메트릭 조회"""
        # 기본 통계
        total_query = select(func.count(TTSGeneration.id)).where(
            and_(
                TTSGeneration.created_at >= start_time,
                TTSGeneration.created_at <= end_time
            )
        )
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        # 완료된 생성
        completed_query = select(func.count(TTSGeneration.id)).where(
            and_(
                TTSGeneration.created_at >= start_time,
                TTSGeneration.created_at <= end_time,
                TTSGeneration.status == GenerationStatus.COMPLETED
            )
        )
        completed_result = await db.execute(completed_query)
        completed_count = completed_result.scalar()
        
        # 실패한 생성
        failed_query = select(func.count(TTSGeneration.id)).where(
            and_(
                TTSGeneration.created_at >= start_time,
                TTSGeneration.created_at <= end_time,
                TTSGeneration.status == GenerationStatus.FAILED
            )
        )
        failed_result = await db.execute(failed_query)
        failed_count = failed_result.scalar()
        
        # 평균 생성 시간 (완료된 것만)
        avg_time_query = select(
            func.avg(TTSGeneration.completed_at - TTSGeneration.started_at)
        ).where(
            and_(
                TTSGeneration.created_at >= start_time,
                TTSGeneration.created_at <= end_time,
                TTSGeneration.status == GenerationStatus.COMPLETED,
                TTSGeneration.started_at.isnot(None),
                TTSGeneration.completed_at.isnot(None)
            )
        )
        avg_time_result = await db.execute(avg_time_query)
        avg_generation_time = avg_time_result.scalar() or 0
        
        # 성공률
        success_rate = (completed_count / total_count * 100) if total_count > 0 else 0
        
        # 일별 분석
        daily_breakdown = await self._get_daily_tts_breakdown(db, start_time, end_time)
        
        # 성우별 분석
        voice_actor_breakdown = await self._get_voice_actor_breakdown(db, start_time, end_time)
        
        return {
            "total_count": total_count,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "avg_generation_time": float(avg_generation_time) if avg_generation_time else 0,
            "success_rate": success_rate,
            "daily_breakdown": daily_breakdown,
            "voice_actor_breakdown": voice_actor_breakdown
        }

    async def get_scenario_metrics(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """시나리오 메트릭 조회"""
        # 활성 시나리오 수
        active_query = select(func.count(Scenario.id)).where(
            Scenario.status == ScenarioStatus.ACTIVE
        )
        active_result = await db.execute(active_query)
        active_count = active_result.scalar()
        
        # 전체 시나리오 수
        total_query = select(func.count(Scenario.id))
        total_result = await db.execute(total_query)
        total_count = total_result.scalar()
        
        # 가장 많이 사용된 시나리오들 (TTS 생성 기준)
        top_scenarios_query = select(
            Scenario.name,
            func.count(TTSGeneration.id).label("usage_count")
        ).select_from(
            Scenario.__table__.join(
                TTSGeneration.__table__,
                Scenario.id == TTSGeneration.script_id  # 실제로는 script를 통해 연결
            )
        ).where(
            TTSGeneration.created_at >= start_time
        ).group_by(
            Scenario.id, Scenario.name
        ).order_by(
            desc("usage_count")
        ).limit(10)
        
        top_result = await db.execute(top_scenarios_query)
        top_scenarios = [
            {"name": name, "usage_count": count}
            for name, count in top_result
        ]
        
        # 배포 통계
        deployment_stats = await self._get_deployment_stats(db, start_time, end_time)
        
        # 상태별 분석
        status_breakdown = await self._get_scenario_status_breakdown(db)
        
        return {
            "active_count": active_count,
            "total_count": total_count,
            "top_scenarios": top_scenarios,
            "deployment_stats": deployment_stats,
            "status_breakdown": status_breakdown
        }

    async def get_health_status(self, db: AsyncSession) -> Dict:
        """시스템 헬스 상태"""
        # 데이터베이스 연결 확인
        try:
            await db.execute(select(1))
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"
        
        # 시스템 리소스 확인
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent(interval=1)
        disk_usage = psutil.disk_usage('/').percent
        
        # 전체 상태 판단
        if db_status == "unhealthy" or memory_usage > 90 or cpu_usage > 90 or disk_usage > 90:
            overall_status = "unhealthy"
        elif memory_usage > 80 or cpu_usage > 80 or disk_usage > 80:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "services": {
                "database": db_status,
                "api": "healthy"  # API가 응답하고 있으므로
            },
            "database": {"status": db_status},
            "storage": {"disk_usage": disk_usage},
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "disk_usage": disk_usage
        }

    async def get_alert_rules(self, db: AsyncSession) -> List:
        """알림 규칙 목록 (구현 예정)"""
        # 여기서는 간단한 더미 데이터 반환
        return []

    async def create_alert_rule(
        self,
        db: AsyncSession,
        rule_in: dict,
        created_by: int
    ) -> dict:
        """알림 규칙 생성 (구현 예정)"""
        # 구현 예정
        return {"id": 1, **rule_in}

    async def get_audit_logs(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """감사 로그 조회"""
        query = select(AuditLog)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        
        if start_time:
            query = query.where(AuditLog.created_at >= start_time)
        
        if end_time:
            query = query.where(AuditLog.created_at <= end_time)
        
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "old_values": log.old_values,
                "new_values": log.new_values,
                "ip_address": str(log.ip_address) if log.ip_address else None,
                "created_at": log.created_at
            }
            for log in logs
        ]

    async def get_system_logs(
        self,
        db: AsyncSession,
        level: Optional[str] = None,
        module: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """시스템 로그 조회"""
        query = select(SystemLog)
        
        if level:
            query = query.where(SystemLog.level == level)
        
        if module:
            query = query.where(SystemLog.module == module)
        
        if start_time:
            query = query.where(SystemLog.created_at >= start_time)
        
        if end_time:
            query = query.where(SystemLog.created_at <= end_time)
        
        query = query.order_by(SystemLog.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "module": log.module,
                "function_name": log.function_name,
                "line_number": log.line_number,
                "exception_info": log.exception_info,
                "extra_data": log.extra_data,
                "created_at": log.created_at
            }
            for log in logs
        ]

    async def record_metric(
        self,
        db: AsyncSession,
        metric_type: str,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        tags: Optional[Dict] = None
    ) -> SystemMetric:
        """메트릭 기록"""
        metric = SystemMetric(
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {}
        )
        
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        
        return metric

    # Private helper methods
    async def _get_count(self, db: AsyncSession, model, *conditions) -> int:
        """테이블 레코드 수 조회"""
        query = select(func.count(model.id))
        for condition in conditions:
            query = query.where(condition)
        
        result = await db.execute(query)
        return result.scalar() or 0

    async def _get_system_health(self) -> Dict:
        """시스템 헬스 상태"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": (disk.used / disk.total) * 100,
                "uptime": psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }

    async def _get_daily_tts_breakdown(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """일별 TTS 생성 분석"""
        query = select(
            func.date(TTSGeneration.created_at).label("date"),
            func.count(TTSGeneration.id).label("total"),
            func.sum(
                func.case(
                    (TTSGeneration.status == GenerationStatus.COMPLETED, 1),
                    else_=0
                )
            ).label("completed")
        ).where(
            and_(
                TTSGeneration.created_at >= start_time,
                TTSGeneration.created_at <= end_time
            )
        ).group_by(
            func.date(TTSGeneration.created_at)
        ).order_by(
            func.date(TTSGeneration.created_at)
        )
        
        result = await db.execute(query)
        return [
            {
                "date": str(date),
                "total": total,
                "completed": completed,
                "success_rate": (completed / total * 100) if total > 0 else 0
            }
            for date, total, completed in result
        ]

    async def _get_voice_actor_breakdown(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict]:
        """성우별 TTS 생성 분석"""
        # 실제 구현에서는 voice_model을 통해 voice_actor와 연결
        query = select(
            VoiceActor.name,
            func.count(TTSGeneration.id).label("total_generations")
        ).select_from(
            VoiceActor.__table__.outerjoin(TTSGeneration.__table__)
        ).where(
            TTSGeneration.created_at >= start_time
        ).group_by(
            VoiceActor.id, VoiceActor.name
        ).order_by(
            desc("total_generations")
        ).limit(10)
        
        result = await db.execute(query)
        return [
            {
                "voice_actor": name,
                "total_generations": count
            }
            for name, count in result
        ]

    async def _get_deployment_stats(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """배포 통계"""
        # 간단한 구현 - 실제로는 Deployment 모델 사용
        return {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "average_deployment_time": 0
        }

    async def _get_scenario_status_breakdown(self, db: AsyncSession) -> List[Dict]:
        """시나리오 상태별 분석"""
        query = select(
            Scenario.status,
            func.count(Scenario.id).label("count")
        ).group_by(
            Scenario.status
        )
        
        result = await db.execute(query)
        return [
            {
                "status": str(status),
                "count": count
            }
            for status, count in result
        ]
