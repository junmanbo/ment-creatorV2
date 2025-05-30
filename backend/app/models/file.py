# app/models/file.py
"""
파일 관련 모델
"""
from sqlalchemy import Boolean, Column, Integer, String, Text

from app.db.base import Base


class FileRecord(Base):
    """파일 레코드 모델"""
    
    __tablename__ = "file_records"
    
    # 기본 정보
    file_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # 파일 정보
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100))
    file_hash = Column(String(64), nullable=False)  # MD5 hash
    
    # 분류 및 메타데이터
    category = Column(String(50), default="general", nullable=False)
    description = Column(Text)
    
    # 사용 통계
    download_count = Column(Integer, default=0, nullable=False)
    
    # 업로드 정보
    uploaded_by = Column(Integer, nullable=True)  # Foreign key to users table
    
    def __repr__(self) -> str:
        return f"<FileRecord(id={self.id}, file_id='{self.file_id}', name='{self.original_name}')>"
