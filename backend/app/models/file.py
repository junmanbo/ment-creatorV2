# app/models/file.py
"""
파일 관련 모델
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class FileRecord(Base):
    """파일 레코드 모델"""
    
    __tablename__ = "file_records"
    
    # 기본 정보
    file_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    original_filename = Column(String(255), nullable=False)  # files.py에서 사용하는 필드명
    file_path = Column(String(500), nullable=False)
    
    # 파일 정보
    file_size = Column(Integer, nullable=False)  # bytes
    content_type = Column(String(100))  # files.py에서 사용하는 필드명
    file_hash = Column(String(64), nullable=False)  # MD5 hash
    
    # 분류 및 메타데이터
    category = Column(String(50), default="general", nullable=False)
    description = Column(Text)
    
    # 사용 통계
    download_count = Column(Integer, default=0, nullable=False)
    
    # 업로드 정보
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 관계
    uploader = relationship("User", foreign_keys=[uploaded_by])
    access_logs = relationship("FileAccessLog", back_populates="file_record", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<FileRecord(id={self.id}, file_id='{self.file_id}', name='{self.original_filename}')>"


class FileAccessLog(Base):
    """파일 접근 로그 모델"""
    
    __tablename__ = "file_access_logs"
    
    # 기본 정보
    file_record_id = Column(Integer, ForeignKey("file_records.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)  # download, stream, view
    
    # 접근 정보
    ip_address = Column(String(45))  # IPv6 지원
    user_agent = Column(Text)
    
    # 접근 시간은 Base에서 created_at으로 처리
    
    # 관계
    file_record = relationship("FileRecord", back_populates="access_logs")
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        return f"<FileAccessLog(id={self.id}, file_id={self.file_record_id}, action='{self.action}')>"
