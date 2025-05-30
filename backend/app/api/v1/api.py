# app/api/v1/api.py
"""
API v1 라우터 통합
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, scenarios, tts, users, voice_actors

api_router = APIRouter()

# 각 도메인별 라우터 포함
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(users.router, prefix="/users", tags=["사용자 관리"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["시나리오 관리"])
api_router.include_router(voice_actors.router, prefix="/voice-actors", tags=["성우 관리"])
api_router.include_router(tts.router, prefix="/tts", tags=["TTS 관리"])
