# app/services/file_service.py
"""
파일 서비스
"""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import UploadFile
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import FileUploadError, NotFoundError
from app.models.file import FileRecord  # 이 모델은 추가로 작성해야 함
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

    async def upload_file(
        self,
        db: AsyncSession,
        file: UploadFile,
        category: str = "general",
        description: Optional[str] = None,
        uploaded_by: Optional[int] = None
    ) -> FileRecord:
        """파일 업로드"""
        try:
            # 파일명 정리
            original_name = file.filename or "unknown"
            sanitized_name = sanitize_filename(original_name)
            
            # 고유 파일명 생성
            file_id = generate_unique_id()
            file_extension = Path(original_name).suffix
            unique_filename = f"{file_id}{file_extension}"
            
            # 카테고리별 디렉토리 생성
            category_dir = self.upload_dir / category
            create_directory_if_not_exists(str(category_dir))
            
            # 파일 경로
            file_path = category_dir / unique_filename
            
            # 파일 저장
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 파일 정보 생성
            file_hash = self._calculate_file_hash(content)
            file_size = len(content)
            mime_type = self._get_mime_type(original_name)
            
            # 데이터베이스 레코드 생성
            file_record = FileRecord(
                file_id=file_id,
                original_name=original_name,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=mime_type,
                file_hash=file_hash,
                category=category,
                description=description,
                uploaded_by=uploaded_by
            )
            
            db.add(file_record)
            await db.commit()
            await db.refresh(file_record)
            
            logger.info(
                "File uploaded successfully",
                file_id=file_id,
                original_name=original_name,
                size=file_size,
                category=category
            )
            
            return file_record
            
        except Exception as e:
            # 업로드된 파일 정리
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            
            logger.error(f"File upload failed: {e}")
            raise FileUploadError(f"파일 업로드에 실패했습니다: {str(e)}")

    async def search_files(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        uploaded_by: Optional[int] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[FileRecord], int]:
        """파일 검색"""
        query = select(FileRecord)
        
        if category:
            query = query.where(FileRecord.category == category)
        
        if file_type:
            query = query.where(FileRecord.mime_type.like(f"{file_type}/%"))
        
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

    async def delete_file(self, db: AsyncSession, file_id: int) -> None:
        """파일 삭제"""
        file_record = await self.get_or_404(db, file_id)
        
        # 실제 파일 삭제
        file_path = Path(file_record.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # 데이터베이스 레코드 삭제
        await self.delete(db, id=file_id)
        
        logger.info(f"File deleted: {file_record.original_name}")

    async def increment_download_count(self, db: AsyncSession, file_id: int) -> None:
        """다운로드 횟수 증가"""
        file_record = await self.get_or_404(db, file_id)
        file_record.download_count += 1
        await db.commit()

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
        
        for category_dir in self.upload_dir.iterdir():
            if category_dir.is_dir():
                for file_path in category_dir.rglob("*"):
                    if file_path.is_file():
                        file_path_str = str(file_path)
                        if file_path_str not in db_file_paths:
                            file_size = get_file_size(file_path_str)
                            orphaned_files.append({
                                "path": file_path_str,
                                "size": file_size,
                                "size_formatted": format_file_size(file_size)
                            })
                            total_size += file_size
                            
                            if not dry_run:
                                file_path.unlink()
        
        return {
            "count": len(orphaned_files),
            "size": total_size,
            "files": orphaned_files
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
                    "name": f.original_name,
                    "size": f.file_size,
                    "created_at": f.created_at
                } for f in recent_uploads
            ],
            "large_files": [
                {
                    "id": f.id,
                    "name": f.original_name,
                    "size": f.file_size,
                    "size_formatted": format_file_size(f.file_size)
                } for f in large_files
            ]
        }

    def _calculate_file_hash(self, content: bytes) -> str:
        """파일 해시 계산"""
        return hashlib.md5(content).hexdigest()

    def _get_mime_type(self, filename: str) -> str:
        """파일 MIME 타입 추정"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
