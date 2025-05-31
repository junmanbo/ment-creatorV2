"""
API v1 라우터 통합
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
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

api_router = APIRouter()

# 각 도메인별 라우터 포함
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(users.router, prefix="/users", tags=["사용자 관리"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["시나리오 관리"])
api_router.include_router(voice_actors.router, prefix="/voice-actors", tags=["성우 관리"])
api_router.include_router(tts.router, prefix="/tts", tags=["TTS 관리"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["시뮬레이션"])
api_router.include_router(deployments.router, prefix="/deployments", tags=["배포 관리"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["모니터링"])
api_router.include_router(files.router, prefix="/files", tags=["파일 관리"])
api_router.include_router(admin.router, prefix="/admin", tags=["관리자"])
