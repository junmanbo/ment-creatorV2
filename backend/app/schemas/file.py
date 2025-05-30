# app/schemas/file.py
"""
파일 관련 스키마
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import PaginatedResponse


class FileBase(BaseModel):
    """파일 기본 스키마"""
    original_name: str = Field(..., description="원본 파일명")
    category: str = Field(default="general", description="파일 카테고리")
    description: Optional[str] = Field(None, description="파일 설명")


class FileCreate(FileBase):
    """파일 생성 스키마"""
    pass


class FileUpdate(BaseModel):
    """파일 수정 스키마"""
    description: Optional[str] = Field(None, description="파일 설명")
    category: Optional[str] = Field(None, description="파일 카테고리")


class FileResponse(FileBase):
    """파일 응답 스키마"""
    id: int = Field(..., description="파일 ID")
    file_id: str = Field(..., description="고유 파일 ID")
    file_path: str = Field(..., description="파일 경로")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    mime_type: Optional[str] = Field(None, description="MIME 타입")
    file_hash: str = Field(..., description="파일 해시")
    download_count: int = Field(default=0, description="다운로드 횟수")
    uploaded_by: Optional[int] = Field(None, description="업로드한 사용자 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 스키마"""
    id: int = Field(..., description="파일 ID")
    file_id: str = Field(..., description="고유 파일 ID")
    original_name: str = Field(..., description="원본 파일명")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    mime_type: Optional[str] = Field(None, description="MIME 타입")
    category: str = Field(..., description="파일 카테고리")
    created_at: datetime = Field(..., description="업로드일시")

    class Config:
        from_attributes = True


class FileListResponse(PaginatedResponse[FileResponse]):
    """파일 목록 응답 스키마"""
    pass


class FileStorageUsage(BaseModel):
    """파일 저장소 사용량 스키마"""
    total_files: int = Field(..., description="총 파일 수")
    total_size: int = Field(..., description="총 크기 (bytes)")
    total_size_formatted: str = Field(..., description="포맷된 크기")
    categories: list = Field(default_factory=list, description="카테고리별 사용량")
    recent_uploads: list = Field(default_factory=list, description="최근 업로드")
    large_files: list = Field(default_factory=list, description="큰 파일들")
