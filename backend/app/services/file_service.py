# app/services/file_service.py
"""
파일 서비스
"""
import hashlib
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import UploadFile, Request
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import FileUploadError, NotFoundError
from app.models.file import FileRecord, FileAccessLog
from app.services.base import BaseService
from app.utils.helpers import (
    create_directory_if_not_exists,
    format_file_size,
    generate_unique_id,
    get_file_size,
    sanitize_filename,
)
from app.utils.logger import logger


class FileService(BaseService[FileRecord]):
    """파일 서비스"""

    def __init__(self):
        super().__init__(FileRecord)
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def create_file_record(
        self,
        db: AsyncSession,
        filename: str,
        file_path: str,
        content_type: Optional[str] = None,
        file_size: Optional[int] = None,
        category: str = "general",
        description: Optional[str] = None,
        uploaded_by: Optional[int] = None
    ) -> FileRecord:
        """파일 레코드 생성"""
        try:
            # 파일 정보 생성
            if file_size is None:
                file_size = get_file_size(file_path)
            
            # 파일 해시 계산
            file_hash = self._calculate_file_hash_from_path(file_path)
            
            # 고유 파일 ID 생성
            file_id = generate_unique_id()
            
            # 데이터베이스 레코드 생성
            file_record = FileRecord(
                file_id=file_id,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                content_type=content_type,
                file_hash=file_hash,
                category=category,
                description=description,
                uploaded_by=uploaded_by
            )
            
            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)
            
            logger.info(
                "File record created",
                file_id=file_id,
                filename=filename,
                size=file_size,
                category=category
            )
            
            return file_record
            
        except Exception as e:
            logger.error(f"File record creation failed: {e}")
            raise FileUploadError(f"파일 레코드 생성에 실패했습니다: {str(e)}")

    async def search_files(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        category: Optional[str] = None,
        uploaded_by: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[FileRecord], int]:
        """파일 검색"""
        query = select(FileRecord)
        
        # 검색 조건 추가
        if search:
            query = query.where(
                FileRecord.original_filename.ilike(f"%{search}%") |
                FileRecord.description.ilike(f"%{search}%")
            )
        
        if category:
            query = query.where(FileRecord.category == category)
        
        if uploaded_by:
            query = query.where(FileRecord.uploaded_by == uploaded_by)
        
        # 총 개수 조회
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 페이징 적용
        query = query.offset(skip).limit(limit).order_by(FileRecord.created_at.desc())
        result = await db.execute(query)
        files = result.scalars().all()
        
        return list(files), total

    async def increment_download_count(self, db: AsyncSession, file_id: int) -> None:
        """다운로드 횟수 증가"""
        file_record = await self.get_or_404(db, file_id)
        file_record.download_count += 1
        await db.commit()

    async def log_file_access(
        self,
        db: AsyncSession,
        file_id: int,
        user_id: int,
        action: str,
        request: Optional[Request] = None
    ) -> None:
        """파일 접근 로그 기록"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        access_log = FileAccessLog(
            file_record_id=file_id,
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(access_log)
        await db.commit()

    async def get_file_access_logs(
        self,
        db: AsyncSession,
        file_id: int,
        limit: int = 50
    ) -> List[dict]:
        """파일 접근 로그 조회"""
        query = (
            select(FileAccessLog)
            .where(FileAccessLog.file_record_id == file_id)
            .order_by(desc(FileAccessLog.created_at))
            .limit(limit)
        )
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at
            }
            for log in logs
        ]

    async def get_file_categories(self, db: AsyncSession) -> List[str]:
        """파일 카테고리 목록 조회"""
        query = select(FileRecord.category).distinct()
        result = await db.execute(query)
        categories = [cat[0] for cat in result.fetchall() if cat[0]]
        return sorted(categories)

    async def get_usage_stats(self, db: AsyncSession, days: int = 30) -> Dict:
        """파일 사용 통계"""
        # 기간 설정
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 총 파일 수와 크기
        total_query = select(
            func.count(FileRecord.id),
            func.sum(FileRecord.file_size)
        )
        total_result = await db.execute(total_query)
        total_files, total_size = total_result.first()
        total_size = total_size or 0
        
        # 일별 업로드 통계
        uploads_query = (
            select(
                func.date(FileRecord.created_at).label('date'),
                func.count(FileRecord.id).label('count')
            )
            .where(FileRecord.created_at >= start_date)
            .group_by(func.date(FileRecord.created_at))
            .order_by(func.date(FileRecord.created_at))
        )
        uploads_result = await db.execute(uploads_query)
        uploads_by_day = [
            {"date": str(date), "count": count}
            for date, count in uploads_result.fetchall()
        ]
        
        # 일별 다운로드 통계 (접근 로그 기반)
        downloads_query = (
            select(
                func.date(FileAccessLog.created_at).label('date'),
                func.count(FileAccessLog.id).label('count')
            )
            .where(
                and_(
                    FileAccessLog.action == 'download',
                    FileAccessLog.created_at >= start_date
                )
            )
            .group_by(func.date(FileAccessLog.created_at))
            .order_by(func.date(FileAccessLog.created_at))
        )
        downloads_result = await db.execute(downloads_query)
        downloads_by_day = [
            {"date": str(date), "count": count}
            for date, count in downloads_result.fetchall()
        ]
        
        # 인기 파일 (다운로드 횟수 기준)
        popular_query = (
            select(FileRecord)
            .order_by(desc(FileRecord.download_count))
            .limit(10)
        )
        popular_result = await db.execute(popular_query)
        popular_files = [
            {
                "id": file.id,
                "filename": file.original_filename,
                "download_count": file.download_count,
                "size": file.file_size
            }
            for file in popular_result.scalars().all()
        ]
        
        # 파일 형식별 통계
        file_types_query = (
            select(
                FileRecord.content_type,
                func.count(FileRecord.id).label('count'),
                func.sum(FileRecord.file_size).label('total_size')
            )
            .group_by(FileRecord.content_type)
            .order_by(desc(func.count(FileRecord.id)))
        )
        file_types_result = await db.execute(file_types_query)
        file_types = [
            {
                "content_type": content_type or "unknown",
                "count": count,
                "total_size": total_size or 0
            }
            for content_type, count, total_size in file_types_result.fetchall()
        ]
        
        # 저장소 사용량
        storage_usage = await self.get_storage_usage(db)
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "uploads_by_day": uploads_by_day,
            "downloads_by_day": downloads_by_day,
            "popular_files": popular_files,
            "file_types": file_types,
            "storage_usage": storage_usage
        }

    async def cleanup_orphaned_files(
        self, 
        db: AsyncSession, 
        dry_run: bool = False
    ) -> Dict:
        """고아 파일 정리"""
        # 데이터베이스에 있는 파일 경로들
        query = select(FileRecord.file_path)
        result = await db.execute(query)
        db_file_paths = set(result.scalars().all())
        
        # 실제 파일 시스템의 파일들
        orphaned_files = []
        total_size = 0
        
        for root, dirs, files in os.walk(self.upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path not in db_file_paths:
                    file_size = get_file_size(file_path)
                    orphaned_files.append({
                        "path": file_path,
                        "size": file_size,
                        "size_formatted": format_file_size(file_size)
                    })
                    total_size += file_size
                    
                    if not dry_run:
                        try:
                            os.remove(file_path)
                        except OSError:
                            pass
        
        return {
            "files": orphaned_files,
            "space": total_size
        }

    async def get_storage_usage(self, db: AsyncSession) -> Dict:
        """저장소 사용량 조회"""
        # 총 파일 수와 크기
        query = select(
            func.count(FileRecord.id),
            func.sum(FileRecord.file_size)
        )
        result = await db.execute(query)
        total_files, total_size = result.first()
        
        total_size = total_size or 0
        
        # 카테고리별 사용량
        category_query = select(
            FileRecord.category,
            func.count(FileRecord.id),
            func.sum(FileRecord.file_size)
        ).group_by(FileRecord.category)
        
        category_result = await db.execute(category_query)
        categories = []
        for category, count, size in category_result:
            categories.append({
                "category": category,
                "file_count": count,
                "total_size": size or 0,
                "total_size_formatted": format_file_size(size or 0)
            })
        
        # 최근 업로드된 파일들 (최근 10개)
        recent_query = select(FileRecord).order_by(
            FileRecord.created_at.desc()
        ).limit(10)
        recent_result = await db.execute(recent_query)
        recent_uploads = recent_result.scalars().all()
        
        # 큰 파일들 (상위 10개)
        large_query = select(FileRecord).order_by(
            FileRecord.file_size.desc()
        ).limit(10)
        large_result = await db.execute(large_query)
        large_files = large_result.scalars().all()
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "total_size_formatted": format_file_size(total_size),
            "categories": categories,
            "recent_uploads": [
                {
                    "id": f.id,
                    "name": f.original_filename,
                    "size": f.file_size,
                    "created_at": f.created_at
                } for f in recent_uploads
            ],
            "large_files": [
                {
                    "id": f.id,
                    "name": f.original_filename,
                    "size": f.file_size,
                    "size_formatted": format_file_size(f.file_size)
                } for f in large_files
            ]
        }

    def _calculate_file_hash(self, content: bytes) -> str:
        """파일 해시 계산"""
        return hashlib.md5(content).hexdigest()

    def _calculate_file_hash_from_path(self, file_path: str) -> str:
        """파일 경로로부터 해시 계산"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _get_mime_type(self, filename: str) -> str:
        """파일 MIME 타입 추정"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
