# app/api/v1/endpoints/files.py
"""
파일 관리 엔드포인트
"""
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_operator_user
from app.api.dependencies.database import get_async_session
from app.api.dependencies.pagination import PaginationParams
from app.core.config import settings
from app.models.user import User
from app.schemas.file import (
    FileListResponse,
    FileResponse as FileResponseSchema,
    FileUploadResponse,
)
from app.services.file_service import FileService
from app.utils.helpers import validate_file_extension

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Query("general", description="파일 카테고리"),
    description: Optional[str] = Query(None, description="파일 설명"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """파일 업로드"""
    # 파일 크기 검증
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # 파일 확장자 검증 (오디오 파일인 경우)
    if category == "audio":
        if not validate_file_extension(file.filename, settings.ALLOWED_FILE_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
            )
    
    file_service = FileService()
    file_record = await file_service.upload_file(
        db,
        file=file,
        category=category,
        description=description,
        uploaded_by=current_user.id
    )
    
    return FileUploadResponse.model_validate(file_record)


@router.get("/", response_model=FileListResponse)
async def get_files(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    file_type: Optional[str] = Query(None, description="파일 타입 필터"),
    uploaded_by: Optional[int] = Query(None, description="업로드한 사용자 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """파일 목록 조회"""
    file_service = FileService()
    files, total = await file_service.search_files(
        db,
        category=category,
        file_type=file_type,
        uploaded_by=uploaded_by,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return FileListResponse(
        items=[FileResponseSchema.model_validate(f) for f in files],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file_info(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """파일 정보 조회"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    return FileResponseSchema.model_validate(file_record)


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """파일 다운로드"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다."
        )
    
    # 다운로드 횟수 증가
    await file_service.increment_download_count(db, file_id)
    
    return FileResponse(
        path=file_path,
        filename=file_record.original_name,
        media_type=file_record.mime_type or "application/octet-stream"
    )


@router.get("/{file_id}/stream")
async def stream_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """파일 스트리밍 (주로 오디오 파일용)"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다."
        )
    
    # 오디오 파일인지 확인
    if not file_record.mime_type or not file_record.mime_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="스트리밍을 지원하지 않는 파일 형식입니다."
        )
    
    def generate_file_stream():
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)  # 8KB 청크
                if not chunk:
                    break
                yield chunk
    
    return StreamingResponse(
        generate_file_stream(),
        media_type=file_record.mime_type,
        headers={
            "Content-Disposition": f"inline; filename={file_record.original_name}",
            "Accept-Ranges": "bytes"
        }
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """파일 삭제"""
    file_service = FileService()
    await file_service.delete_file(db, file_id)


@router.get("/audio/{audio_id}/stream")
async def stream_audio(
    audio_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """오디오 파일 스트리밍 (별칭)"""
    return await stream_file(audio_id, db, _)


@router.get("/audio/{audio_id}/download")
async def download_audio(
    audio_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """오디오 파일 다운로드 (별칭)"""
    return await download_file(audio_id, db, _)


@router.post("/cleanup")
async def cleanup_orphaned_files(
    dry_run: bool = Query(False, description="실제 삭제하지 않고 미리보기만"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """고아 파일 정리"""
    file_service = FileService()
    result = await file_service.cleanup_orphaned_files(db, dry_run=dry_run)
    
    return {
        "orphaned_files_count": result["count"],
        "total_size_freed": result["size"],
        "dry_run": dry_run,
        "files": result["files"] if dry_run else []
    }


@router.get("/storage/usage")
async def get_storage_usage(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """저장소 사용량 조회"""
    file_service = FileService()
    usage_info = await file_service.get_storage_usage(db)
    
    return {
        "total_files": usage_info["total_files"],
        "total_size": usage_info["total_size"],
        "total_size_formatted": usage_info["total_size_formatted"],
        "categories": usage_info["categories"],
        "recent_uploads": usage_info["recent_uploads"],
        "large_files": usage_info["large_files"]
    }


@router.post("/batch-upload", response_model=List[FileUploadResponse])
async def batch_upload_files(
    files: List[UploadFile] = File(...),
    category: Optional[str] = Query("general", description="파일 카테고리"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """배치 파일 업로드"""
    if len(files) > 10:  # 최대 10개 파일
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="한 번에 최대 10개의 파일만 업로드할 수 있습니다."
        )
    
    file_service = FileService()
    uploaded_files = []
    
    for file in files:
        # 개별 파일 검증
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"파일 '{file.filename}'의 크기가 너무 큽니다."
            )
        
        try:
            file_record = await file_service.upload_file(
                db,
                file=file,
                category=category,
                uploaded_by=current_user.id
            )
            uploaded_files.append(FileUploadResponse.model_validate(file_record))
        except Exception as e:
            # 실패한 파일은 건너뛰고 계속 진행
            continue
    
    return uploaded_files
