# app/services/admin_service.py
"""
관리자 서비스
"""
import json
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.security import security
from app.models.audit import AuditLog, SystemLog
from app.models.monitoring import SystemMetric
from app.models.scenario import Scenario
from app.models.tts import TTSGeneration
from app.models.user import User
from app.models.voice_actor import VoiceActor
from app.services.base import BaseService
from app.utils.logger import logger


class AdminService(BaseService):
    """관리자 서비스"""

    def __init__(self):
        super().__init__(User)  # 기본 모델로 User 사용

    async def get_system_settings(self, db: AsyncSession) -> Dict:
        """시스템 설정 조회"""
        # 실제 구현에서는 별도의 settings 테이블을 사용할 수 있음
        # 여기서는 환경변수 기반으로 구현
        return {
            "project_name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "max_file_size": settings.MAX_FILE_SIZE,
            "allowed_file_extensions": settings.ALLOWED_FILE_EXTENSIONS,
            "default_page_size": settings.DEFAULT_PAGE_SIZE,
            "max_page_size": settings.MAX_PAGE_SIZE,
            "tts_max_text_length": settings.TTS_MAX_TEXT_LENGTH,
            "tts_generation_timeout": settings.TTS_GENERATION_TIMEOUT,
            "rate_limits": {
                "general": settings.RATE_LIMIT_GENERAL,
                "tts": settings.RATE_LIMIT_TTS,
                "upload": settings.RATE_LIMIT_UPLOAD,
                "simulation": settings.RATE_LIMIT_SIMULATION
            }
        }

    async def update_system_settings(
        self,
        db: AsyncSession,
        settings_update: dict,
        updated_by: int
    ) -> Dict:
        """시스템 설정 변경"""
        # 설정 변경 로깅
        logger.info(
            "System settings updated",
            updated_by=updated_by,
            changes=settings_update
        )
        
        # 감사 로그 기록
        audit_log = AuditLog(
            user_id=updated_by,
            action="UPDATE_SYSTEM_SETTINGS",
            resource_type="system_settings",
            resource_id="global",
            new_values=settings_update
        )
        db.add(audit_log)
        await db.commit()
        
        # 업데이트된 설정 반환 (실제로는 새로운 설정을 적용해야 함)
        current_settings = await self.get_system_settings(db)
        current_settings.update(settings_update)
        
        return current_settings

    async def get_system_overview(self, db: AsyncSession) -> Dict:
        """시스템 개요 통계"""
        # 사용자 통계
        user_count = await self._get_count(db, User)
        active_user_count = await self._get_count(db, User, User.is_active == True)
        
        # 시나리오 통계
        scenario_count = await self._get_count(db, Scenario)
        active_scenario_count = await self._get_count(db, Scenario, Scenario.status == "active")
        
        # 성우 통계
        voice_actor_count = await self._get_count(db, VoiceActor)
        
        # TTS 통계
        today = datetime.utcnow().date()
        tts_today = await self._get_count(
            db, TTSGeneration,
            func.date(TTSGeneration.created_at) == today
        )
        tts_total = await self._get_count(db, TTSGeneration)
        
        # 저장소 사용량
        storage_usage = await self._get_storage_usage()
        
        # 시스템 상태
        health_status = await self._get_health_status()
        
        # 시스템 가동 시간
        uptime = time.time() - psutil.boot_time()
        
        return {
            "user_count": user_count,
            "active_user_count": active_user_count,
            "scenario_count": scenario_count,
            "active_scenario_count": active_scenario_count,
            "voice_actor_count": voice_actor_count,
            "tts_today": tts_today,
            "tts_total": tts_total,
            "storage_usage": storage_usage,
            "health_status": health_status,
            "uptime": uptime
        }

    async def get_detailed_stats(self, db: AsyncSession, days: int = 30) -> Dict:
        """상세 시스템 통계"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # 사용자 활동
        user_activity = await self._get_user_activity_stats(db, start_time, end_time)
        
        # TTS 사용량
        tts_usage = await self._get_tts_usage_stats(db, start_time, end_time)
        
        # 시나리오 사용량
        scenario_usage = await self._get_scenario_usage_stats(db, start_time, end_time)
        
        # 에러율
        error_rates = await self._get_error_rates(db, start_time, end_time)
        
        # 성능 메트릭
        performance_metrics = await self._get_performance_metrics(db, start_time, end_time)
        
        # 리소스 사용량
        resource_usage = await self._get_resource_usage_history(db, start_time, end_time)
        
        return {
            "user_activity": user_activity,
            "tts_usage": tts_usage,
            "scenario_usage": scenario_usage,
            "error_rates": error_rates,
            "performance_metrics": performance_metrics,
            "resource_usage": resource_usage
        }

    async def get_database_status(self, db: AsyncSession) -> Dict:
        """데이터베이스 상태 조회"""
        try:
            # 연결 수 조회
            connections_query = text("""
                SELECT count(*) as connections
                FROM pg_stat_activity
                WHERE state = 'active'
            """)
            connections_result = await db.execute(connections_query)
            connections = connections_result.scalar()
            
            # 활성 쿼리 수
            active_queries_query = text("""
                SELECT count(*) as active_queries
                FROM pg_stat_activity
                WHERE state = 'active' AND query != '<IDLE>'
            """)
            active_queries_result = await db.execute(active_queries_query)
            active_queries = active_queries_result.scalar()
            
            # 데이터베이스 크기
            size_query = text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size_result = await db.execute(size_query)
            size = size_result.scalar()
            
            # 테이블 크기들
            table_sizes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            table_sizes_result = await db.execute(table_sizes_query)
            table_sizes = [
                {"schema": schema, "table": table, "size": size}
                for schema, table, size in table_sizes_result
            ]
            
            return {
                "connections": connections,
                "active_queries": active_queries,
                "size": size,
                "table_sizes": table_sizes,
                "index_usage": [],  # 구현 예정
                "slow_queries": []  # 구현 예정
            }
            
        except Exception as e:
            logger.error(f"Failed to get database status: {e}")
            return {
                "connections": 0,
                "active_queries": 0,
                "size": "Unknown",
                "table_sizes": [],
                "index_usage": [],
                "slow_queries": [],
                "error": str(e)
            }

    async def optimize_database(self, db: AsyncSession, analyze_only: bool = False) -> Dict:
        """데이터베이스 최적화"""
        try:
            optimized_tables = []
            space_freed = 0
            
            if not analyze_only:
                # VACUUM ANALYZE 실행
                tables_query = text("""
                    SELECT tablename FROM pg_tables WHERE schemaname = 'public'
                """)
                tables_result = await db.execute(tables_query)
                tables = [table[0] for table in tables_result]
                
                for table in tables:
                    try:
                        vacuum_query = text(f"VACUUM ANALYZE {table}")
                        await db.execute(vacuum_query)
                        optimized_tables.append(table)
                    except Exception as e:
                        logger.warning(f"Failed to vacuum table {table}: {e}")
            
            return {
                "performed": not analyze_only,
                "tables": optimized_tables,
                "space_freed": space_freed,
                "improvement": "Database optimization completed" if not analyze_only else "Analysis completed"
            }
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            raise ValidationError(f"데이터베이스 최적화에 실패했습니다: {str(e)}")

    async def create_backup(
        self,
        db: AsyncSession,
        backup_type: str = "full",
        include_files: bool = True,
        compression: bool = True,
        created_by: int = None
    ) -> Dict:
        """시스템 백업 생성"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            
            # 백업 디렉토리 생성
            backup_dir = Path(f"/tmp/{backup_name}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 데이터베이스 백업
            if backup_type in ["full", "database"]:
                db_backup_path = backup_dir / "database.sql"
                # pg_dump 명령 실행 (실제 환경에 맞게 수정 필요)
                # subprocess.run([
                #     "pg_dump", 
                #     settings.DATABASE_URL_SYNC,
                #     "-f", str(db_backup_path)
                # ], check=True)
            
            # 파일 백업
            if include_files and backup_type in ["full", "files"]:
                files_backup_dir = backup_dir / "files"
                files_backup_dir.mkdir(exist_ok=True)
                
                # 업로드된 파일들 복사
                if Path(settings.UPLOAD_DIR).exists():
                    shutil.copytree(
                        settings.UPLOAD_DIR,
                        files_backup_dir / "uploads",
                        dirs_exist_ok=True
                    )
                
                # 오디오 파일들 복사
                if Path(settings.AUDIO_DIR).exists():
                    shutil.copytree(
                        settings.AUDIO_DIR,
                        files_backup_dir / "audio",
                        dirs_exist_ok=True
                    )
            
            # 압축
            if compression:
                archive_path = f"{backup_dir}.tar.gz"
                shutil.make_archive(backup_dir, 'gztar', backup_dir)
                shutil.rmtree(backup_dir)  # 원본 디렉토리 삭제
                backup_path = archive_path
            else:
                backup_path = str(backup_dir)
            
            # 백업 정보 기록 (실제로는 Backup 모델에 저장)
            backup_info = {
                "id": hash(backup_name) % 1000000,  # 임시 ID
                "name": backup_name,
                "type": backup_type,
                "path": backup_path,
                "size": self._get_directory_size(backup_path),
                "compressed": compression,
                "created_by": created_by,
                "created_at": datetime.utcnow()
            }
            
            logger.info(f"Backup created: {backup_name}")
            return backup_info
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            raise ValidationError(f"백업 생성에 실패했습니다: {str(e)}")

    async def get_backups(self, db: AsyncSession, limit: int = 20) -> List[Dict]:
        """백업 목록 조회"""
        # 실제로는 Backup 모델에서 조회
        # 여기서는 더미 데이터 반환
        return [
            {
                "id": 1,
                "name": "backup_full_20250530_120000",
                "type": "full",
                "size": 1024 * 1024 * 100,  # 100MB
                "created_at": datetime.utcnow() - timedelta(days=1),
                "created_by": 1
            }
        ]

    async def restore_backup(
        self,
        db: AsyncSession,
        backup_id: int,
        restored_by: int
    ) -> Dict:
        """백업 복원"""
        # 실제 구현에서는 백업 파일을 찾아서 복원
        logger.warning(f"Backup restore requested: {backup_id} by user {restored_by}")
        
        return {
            "status": "completed",
            "tables": ["users", "scenarios", "voice_actors"],
            "files": ["uploads", "audio"],
            "time": 120  # 초
        }

    async def delete_backup(self, db: AsyncSession, backup_id: int) -> None:
        """백업 삭제"""
        # 실제 구현에서는 백업 파일도 함께 삭제
        logger.info(f"Backup deleted: {backup_id}")

    async def set_maintenance_mode(
        self,
        db: AsyncSession,
        enabled: bool,
        message: Optional[str] = None,
        estimated_duration: Optional[int] = None,
        set_by: int = None
    ) -> Dict:
        """유지보수 모드 설정"""
        # 실제로는 별도의 설정 저장소에 저장
        maintenance_info = {
            "enabled": enabled,
            "message": message or ("시스템 유지보수 중입니다." if enabled else ""),
            "duration": estimated_duration,
            "set_at": datetime.utcnow(),
            "set_by": set_by
        }
        
        # 감사 로그 기록
        audit_log = AuditLog(
            user_id=set_by,
            action="SET_MAINTENANCE_MODE",
            resource_type="system",
            resource_id="maintenance",
            new_values=maintenance_info
        )
        db.add(audit_log)
        await db.commit()
        
        logger.info(f"Maintenance mode {'enabled' if enabled else 'disabled'} by user {set_by}")
        return maintenance_info

    async def get_maintenance_status(self, db: AsyncSession) -> Dict:
        """유지보수 모드 상태 조회"""
        # 실제로는 설정 저장소에서 조회
        return {
            "enabled": False,
            "message": "",
            "duration": None,
            "set_at": None,
            "set_by": None
        }

    async def clear_cache(self, db: AsyncSession, cache_type: Optional[str] = None) -> Dict:
        """캐시 정리"""
        cleared_items = 0
        size_freed = 0
        start_time = time.time()
        
        try:
            if cache_type in [None, "all", "file"]:
                # 파일 캐시 정리
                temp_files = list(Path("/tmp").glob("ars_*"))
                for temp_file in temp_files:
                    if temp_file.is_file():
                        size_freed += temp_file.stat().st_size
                        temp_file.unlink()
                        cleared_items += 1
            
            if cache_type in [None, "all", "redis"]:
                # Redis 캐시 정리 (실제 Redis 연결 시)
                pass
            
            time_taken = time.time() - start_time
            
            logger.info(f"Cache cleared: {cleared_items} items, {size_freed} bytes")
            return {
                "items": cleared_items,
                "size": size_freed,
                "time": time_taken
            }
            
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            raise ValidationError(f"캐시 정리에 실패했습니다: {str(e)}")

    async def get_system_logs(
        self,
        db: AsyncSession,
        level: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """시스템 로그 조회"""
        query = select(SystemLog).order_by(SystemLog.created_at.desc())
        
        if level:
            query = query.where(SystemLog.level == level)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "level": log.level,
                "message": log.message,
                "module": log.module,
                "created_at": log.created_at
            }
            for log in logs
        ]

    async def get_audit_logs(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """감사 로그 조회"""
        query = select(AuditLog).order_by(AuditLog.created_at.desc())
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if action:
            query = query.where(AuditLog.action == action)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "created_at": log.created_at
            }
            for log in logs
        ]

    async def run_cleanup_tasks(
        self,
        db: AsyncSession,
        task_type: str = "all",
        dry_run: bool = False
    ) -> Dict:
        """정리 작업 실행"""
        results = {}
        total_cleaned = 0
        size_freed = 0
        
        if task_type in ["all", "temp_files"]:
            # 임시 파일 정리
            temp_result = await self._cleanup_temp_files(dry_run)
            results["temp_files"] = temp_result
            total_cleaned += temp_result["count"]
            size_freed += temp_result["size"]
        
        if task_type in ["all", "old_logs"]:
            # 오래된 로그 정리
            log_result = await self._cleanup_old_logs(db, dry_run)
            results["old_logs"] = log_result
            total_cleaned += log_result["count"]
        
        if task_type in ["all", "orphaned_files"]:
            # 고아 파일 정리
            orphan_result = await self._cleanup_orphaned_files(db, dry_run)
            results["orphaned_files"] = orphan_result
            total_cleaned += orphan_result["count"]
            size_freed += orphan_result["size"]
        
        return {
            "results": results,
            "total": total_cleaned,
            "size_freed": size_freed
        }

    async def create_impersonation_token(
        self,
        db: AsyncSession,
        target_user_id: int,
        admin_user_id: int,
        duration_minutes: int = 60
    ) -> Dict:
        """사용자 대신 로그인 토큰 생성"""
        # 대상 사용자 확인
        target_user = await self.get_or_404(db, target_user_id)
        
        # 만료 시간
        expires_at = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        # 임시 토큰 생성
        token_data = {
            "sub": str(target_user_id),
            "admin_id": admin_user_id,
            "impersonation": True,
            "exp": expires_at.timestamp()
        }
        
        token = security.create_access_token(
            subject=target_user_id,
            expires_delta=timedelta(minutes=duration_minutes)
        )
        
        # 감사 로그 기록
        audit_log = AuditLog(
            user_id=admin_user_id,
            action="IMPERSONATE_USER",
            resource_type="user",
            resource_id=str(target_user_id),
            new_values={"duration_minutes": duration_minutes}
        )
        db.add(audit_log)
        await db.commit()
        
        logger.warning(
            f"User impersonation: admin {admin_user_id} -> user {target_user_id}"
        )
        
        return {
            "token": token,
            "expires_at": expires_at
        }

    async def get_detailed_health(self, db: AsyncSession) -> Dict:
        """상세 헬스 체크"""
        components = {
            "database": await self._check_database_health(db),
            "storage": await self._check_storage_health(),
            "memory": await self._check_memory_health(),
            "services": await self._check_services_health()
        }
        
        # 전체 상태 결정
        overall_status = "healthy"
        alerts = []
        recommendations = []
        
        for component, status in components.items():
            if status["status"] == "unhealthy":
                overall_status = "unhealthy"
                alerts.append(f"{component} is unhealthy: {status.get('message', '')}")
            elif status["status"] == "warning" and overall_status == "healthy":
                overall_status = "warning"
        
        # 성능 메트릭
        performance = {
            "response_time": await self._get_average_response_time(db),
            "throughput": await self._get_throughput_metrics(db),
            "error_rate": await self._get_error_rate(db)
        }
        
        return {
            "status": overall_status,
            "components": components,
            "performance": performance,
            "alerts": alerts,
            "recommendations": recommendations
        }

    # Private helper methods
    async def _get_count(self, db: AsyncSession, model, *conditions) -> int:
        """레코드 수 조회"""
        query = select(func.count(model.id))
        for condition in conditions:
            query = query.where(condition)
        
        result = await db.execute(query)
        return result.scalar() or 0

    async def _get_storage_usage(self) -> Dict:
        """저장소 사용량"""
        try:
            disk_usage = psutil.disk_usage('/')
            return {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": (disk_usage.used / disk_usage.total) * 100
            }
        except Exception:
            return {"error": "Unable to get storage usage"}

    async def _get_health_status(self) -> str:
        """헬스 상태"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            
            if memory.percent > 90 or cpu > 90:
                return "critical"
            elif memory.percent > 80 or cpu > 80:
                return "warning"
            else:
                return "healthy"
        except Exception:
            return "unknown"

    def _get_directory_size(self, path: str) -> int:
        """디렉토리 크기 계산"""
        try:
            if Path(path).is_file():
                return Path(path).stat().st_size
            else:
                total = 0
                for p in Path(path).rglob("*"):
                    if p.is_file():
                        total += p.stat().st_size
                return total
        except Exception:
            return 0

    async def _cleanup_temp_files(self, dry_run: bool = False) -> Dict:
        """임시 파일 정리"""
        temp_dir = Path("/tmp")
        cleaned_files = []
        total_size = 0
        
        for temp_file in temp_dir.glob("ars_*"):
            if temp_file.is_file():
                size = temp_file.stat().st_size
                cleaned_files.append(str(temp_file))
                total_size += size
                
                if not dry_run:
                    temp_file.unlink()
        
        return {
            "count": len(cleaned_files),
            "size": total_size,
            "files": cleaned_files if dry_run else []
        }

    async def _cleanup_old_logs(self, db: AsyncSession, dry_run: bool = False) -> Dict:
        """오래된 로그 정리"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # 30일 이상 된 시스템 로그 삭제
        old_logs_query = select(SystemLog).where(
            SystemLog.created_at < cutoff_date
        )
        result = await db.execute(old_logs_query)
        old_logs = result.scalars().all()
        
        if not dry_run:
            for log in old_logs:
                await db.delete(log)
            await db.commit()
        
        return {
            "count": len(old_logs),
            "cutoff_date": cutoff_date
        }

    async def _cleanup_orphaned_files(self, db: AsyncSession, dry_run: bool = False) -> Dict:
        """고아 파일 정리"""
        # 파일 서비스의 cleanup_orphaned_files 메서드 사용
        from app.services.file_service import FileService
        
        file_service = FileService()
        result = await file_service.cleanup_orphaned_files(db, dry_run=dry_run)
        
        return result

    # Health check methods
    async def _check_database_health(self, db: AsyncSession) -> Dict:
        """데이터베이스 헬스 체크"""
        try:
            await db.execute(select(1))
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_storage_health(self) -> Dict:
        """저장소 헬스 체크"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            if usage_percent > 90:
                return {"status": "unhealthy", "usage": usage_percent}
            elif usage_percent > 80:
                return {"status": "warning", "usage": usage_percent}
            else:
                return {"status": "healthy", "usage": usage_percent}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_memory_health(self) -> Dict:
        """메모리 헬스 체크"""
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                return {"status": "unhealthy", "usage": memory.percent}
            elif memory.percent > 80:
                return {"status": "warning", "usage": memory.percent}
            else:
                return {"status": "healthy", "usage": memory.percent}
        except Exception as e:
            return {"status": "unhealthy", "message": str(e)}

    async def _check_services_health(self) -> Dict:
        """서비스 헬스 체크"""
        return {"status": "healthy", "services": ["api", "database"]}

    # Performance metrics methods
    async def _get_average_response_time(self, db: AsyncSession) -> float:
        """평균 응답 시간"""
        # 구현 예정
        return 0.0

    async def _get_throughput_metrics(self, db: AsyncSession) -> Dict:
        """처리량 메트릭"""
        # 구현 예정
        return {"requests_per_second": 0.0}

    async def _get_error_rate(self, db: AsyncSession) -> float:
        """에러율"""
        # 구현 예정
        return 0.0

    # Statistics methods
    async def _get_user_activity_stats(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> Dict:
        """사용자 활동 통계"""
        # 구현 예정
        return {"daily_active_users": [], "total_sessions": 0}

    async def _get_tts_usage_stats(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> Dict:
        """TTS 사용량 통계"""
        # 구현 예정
        return {"total_generations": 0, "success_rate": 0.0}

    async def _get_scenario_usage_stats(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> Dict:
        """시나리오 사용량 통계"""
        # 구현 예정
        return {"most_used": [], "total_usage": 0}

    async def _get_error_rates(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> Dict:
        """에러율"""
        # 구현 예정
        return {"total_errors": 0, "error_rate": 0.0}

    async def _get_performance_metrics(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> Dict:
        """성능 메트릭"""
        # 구현 예정
        return {"avg_response_time": 0.0, "throughput": 0.0}

    async def _get_resource_usage_history(self, db: AsyncSession, start_time: datetime, end_time: datetime) -> Dict:
        """리소스 사용량 이력"""
        # 구현 예정
        return {"cpu": [], "memory": [], "disk": []}
