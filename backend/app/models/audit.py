"""
감사 및 로그 모델
"""

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class AuditLog(Base):
    """감사 로그"""

    __tablename__ = "audit_logs"

    # 기본 정보
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))

    # 변경 내용
    old_values = Column(JSONB)
    new_values = Column(JSONB)

    # 요청 정보
    ip_address = Column(INET)
    user_agent = Column(Text)

    # 관계
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource_type='{self.resource_type}')>"


class SystemLog(Base):
    """시스템 로그"""

    __tablename__ = "system_logs"

    # 기본 정보
    level = Column(String(20), nullable=False)  # LogLevel enum을 문자열로 저장
    message = Column(Text, nullable=False)
    module = Column(String(100))
    function_name = Column(String(100))
    line_number = Column(Integer)

    # 예외 정보
    exception_info = Column(Text)
    extra_data = Column(JSONB)

    def __repr__(self) -> str:
        return (
            f"<SystemLog(id={self.id}, level='{self.level}', module='{self.module}')>"
        )
