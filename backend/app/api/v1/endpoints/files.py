"""
파일 관리 엔드포인트
"""
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
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
    FileCategoriesResponse,
    FileUsageStatsResponse,
    OrphanedFilesResponse,
)
from app.services.file_service import FileService
from app.utils.helpers import save_upload_file, validate_file_extension

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description="업로드할 파일"),
    category: Optional[str] = Query(None, description="파일 카테고리"),
    description: Optional[str] = Query(None, description="파일 설명"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """파일 업로드"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 필요합니다."
        )
    
    # 파일 확장자 검증
    if not validate_file_extension(file.filename, settings.ALLOWED_FILE_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
        )
    
    # 파일 크기 확인
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    # 파일 저장
    file_path = await save_upload_file(file, directory=settings.UPLOAD_DIR)
    
    # 파일 정보 데이터베이스에 저장
    file_service = FileService()
    file_record = await file_service.create_file_record(
        db,
        filename=file.filename,
        file_path=file_path,
        content_type=file.content_type,
        file_size=file.size,
        category=category,
        description=description,
        uploaded_by=current_user.id
    )
    
    return FileUploadResponse.model_validate(file_record)


@router.get("/", response_model=FileListResponse)
async def get_files(
    pagination: PaginationParams = Depends(),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    search: Optional[str] = Query(None, description="파일명 검색"),
    uploaded_by: Optional[int] = Query(None, description="업로더 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """파일 목록 조회"""
    file_service = FileService()
    files, total = await file_service.search_files(
        db,
        search=search,
        category=category,
        uploaded_by=uploaded_by,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return FileListResponse(
        items=[FileResponseSchema.model_validate(file) for file in files],
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
    current_user: User = Depends(get_current_active_user)
):
    """파일 다운로드"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    
    # 파일 존재 확인
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다."
        )
    
    # 다운로드 카운트 증가
    await file_service.increment_download_count(db, file_id)
    
    # 접근 로그 기록
    await file_service.log_file_access(
        db,
        file_id=file_id,
        user_id=current_user.id,
        action="download"
    )
    
    return FileResponse(
        file_record.file_path,
        media_type=file_record.content_type or "application/octet-stream",
        filename=file_record.original_filename
    )


@router.get("/{file_id}/stream")
async def stream_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_active_user)
):
    """파일 스트리밍 (이미지, 오디오, 비디오 등)"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    
    # 파일 존재 확인
    if not os.path.exists(file_record.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다."
        )
    
    # 스트리밍 가능 파일 타입 확인
    streamable_types = ["image/", "audio/", "video/", "text/"]
    if not any(file_record.content_type.startswith(t) for t in streamable_types if file_record.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="스트리밍할 수 없는 파일 형식입니다."
        )
    
    # 접근 로그 기록
    await file_service.log_file_access(
        db,
        file_id=file_id,
        user_id=current_user.id,
        action="stream"
    )
    
    return FileResponse(
        file_record.file_path,
        media_type=file_record.content_type
    )


@router.put("/{file_id}", response_model=FileResponseSchema)
async def update_file_info(
    file_id: int,
    category: Optional[str] = Query(None, description="카테고리"),
    description: Optional[str] = Query(None, description="설명"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """파일 정보 수정"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    
    # 파일 소유자이거나 관리자/매니저인 경우만 수정 가능
    if (file_record.uploaded_by != current_user.id and 
        current_user.role not in ["admin", "manager"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="파일 정보를 수정할 권한이 없습니다."
        )
    
    # 정보 업데이트
    update_data = {}
    if category is not None:
        update_data["category"] = category
    if description is not None:
        update_data["description"] = description
    
    if update_data:
        updated_file = await file_service.update(
            db,
            db_obj=file_record,
            obj_in=update_data
        )
        return FileResponseSchema.model_validate(updated_file)
    
    return FileResponseSchema.model_validate(file_record)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """파일 삭제"""
    file_service = FileService()
    file_record = await file_service.get_or_404(db, file_id)
    
    # 파일 소유자이거나 관리자/매니저인 경우만 삭제 가능
    if (file_record.uploaded_by != current_user.id and 
        current_user.role not in ["admin", "manager"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="파일을 삭제할 권한이 없습니다."
        )
    
    # 물리적 파일 삭제
    if os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
        except OSError:
            pass  # 파일 삭제 실패는 무시 (이미 삭제되었을 수 있음)
    
    # 데이터베이스에서 삭제
    await file_service.delete(db, id=file_id)


@router.get("/{file_id}/access-log")
async def get_file_access_log(
    file_id: int,
    limit: int = Query(50, description="조회 개수"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """파일 접근 로그 조회"""
    file_service = FileService()
    
    # 파일 존재 확인
    await file_service.get_or_404(db, file_id)
    
    # 접근 로그 조회
    access_logs = await file_service.get_file_access_logs(
        db,
        file_id=file_id,
        limit=limit
    )
    
    return {
        "file_id": file_id,
        "access_logs": access_logs,
        "total_accesses": len(access_logs)
    }


@router.post("/bulk-upload", response_model=List[FileUploadResponse])
async def bulk_upload_files(
    files: List[UploadFile] = File(..., description="업로드할 파일들"),
    category: Optional[str] = Query(None, description="파일 카테고리"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """대량 파일 업로드"""
    if len(files) > 10:  # 최대 10개 파일
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="한 번에 최대 10개의 파일만 업로드할 수 있습니다."
        )
    
    file_service = FileService()
    uploaded_files = []
    
    for file in files:
        if not file.filename:
            continue
            
        # 개별 파일 검증
        if not validate_file_extension(file.filename, settings.ALLOWED_FILE_EXTENSIONS):
            continue
            
        if file.size and file.size > settings.MAX_FILE_SIZE:
            continue
        
        try:
            # 파일 저장
            file_path = await save_upload_file(file, directory=settings.UPLOAD_DIR)
            
            # 데이터베이스에 기록
            file_record = await file_service.create_file_record(
                db,
                filename=file.filename,
                file_path=file_path,
                content_type=file.content_type,
                file_size=file.size,
                category=category,
                uploaded_by=current_user.id
            )
            
            uploaded_files.append(FileUploadResponse.model_validate(file_record))
            
        except Exception:
            # 개별 파일 업로드 실패 시 계속 진행
            continue
    
    return uploaded_files


@router.get("/categories/list", response_model=FileCategoriesResponse)
async def get_file_categories(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """파일 카테고리 목록 조회"""
    file_service = FileService()
    categories = await file_service.get_file_categories(db)
    return FileCategoriesResponse(
        categories=categories,
        total=len(categories)
    )


@router.get("/stats/usage", response_model=FileUsageStatsResponse)
async def get_file_usage_stats(
    days: int = Query(30, description="조회 기간 (일)"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """파일 사용 통계"""
    file_service = FileService()
    stats = await file_service.get_usage_stats(db, days=days)
    return FileUsageStatsResponse(**stats)


@router.post("/cleanup/orphaned", response_model=OrphanedFilesResponse)
async def cleanup_orphaned_files(
    dry_run: bool = Query(True, description="미리보기 모드"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """고아 파일 정리"""
    file_service = FileService()
    result = await file_service.cleanup_orphaned_files(db, dry_run=dry_run)
    return OrphanedFilesResponse(
        dry_run=dry_run,
        orphaned_files=result["files"],
        total_files=len(result["files"]),
        space_to_free=result["space"],
        cleaned=not dry_run
    )
