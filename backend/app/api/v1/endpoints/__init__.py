# app/api/v1/endpoints/__init__.py
"""
API v1 엔드포인트 모듈 초기화
"""

# 모든 엔드포인트 라우터들을 import하여 사용 가능하게 함
from . import (
    admin,
    auth,
    deployments,
    files,
    monitoring,
    scenarios,
    simulations,
    tts,
    users,
    voice_actors,
)

__all__ = [
    "admin",
    "auth",
    "deployments", 
    "files",
    "monitoring",
    "scenarios",
    "simulations",
    "tts",
    "users",
    "voice_actors",
]
