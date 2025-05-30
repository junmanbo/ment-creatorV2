# app/api/v1/endpoints/voice_actors.py
"""
성우 관리 엔드포인트
"""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_operator_user
from app.api.dependencies.database import get_async_session
from app.api.dependencies.pagination import PaginationParams, SearchParams
from app.core.config import settings
from app.models.user import User
from app.schemas.voice_actor import (
    VoiceActorCreate,
    VoiceActorListResponse,
    VoiceActorResponse,
    VoiceActorUpdate,
    VoiceModelCreate,
    VoiceModelResponse,
    VoiceSampleCreate,
    VoiceSampleResponse,
)
from app.services.voice_service import VoiceActorService, VoiceModelService, VoiceSampleService
from app.utils.constants import AgeRangeType, GenderType
from app.utils.helpers import save_upload_file, validate_file_extension

router = APIRouter()


# 성우 관리
@router.get("/", response_model=VoiceActorListResponse)
async def get_voice_actors(
    pagination: PaginationParams = Depends(),
    search: SearchParams = Depends(),
    gender: Optional[GenderType] = Query(None, description="성별 필터"),
    age_range: Optional[AgeRangeType] = Query(None, description="연령대 필터"),
    language: Optional[str] = Query(None, description="언어 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """성우 목록 조회"""
    voice_actor_service = VoiceActorService()
    actors, total = await voice_actor_service.search_voice_actors(
        db,
        search=search.search,
        gender=gender,
        age_range=age_range,
        language=language,
        is_active=is_active,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return VoiceActorListResponse(
        items=[VoiceActorResponse.model_validate(actor) for actor in actors],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.get("/{actor_id}", response_model=VoiceActorResponse)
async def get_voice_actor(
    actor_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """특정 성우 조회"""
    voice_actor_service = VoiceActorService()
    actor = await voice_actor_service.get_or_404(db, actor_id)
    return VoiceActorResponse.model_validate(actor)


@router.post("/", response_model=VoiceActorResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_actor(
    actor_in: VoiceActorCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """새 성우 생성"""
    voice_actor_service = VoiceActorService()
    actor = await voice_actor_service.create_voice_actor(
        db,
        voice_actor_in=actor_in,
        created_by=current_user.id
    )
    return VoiceActorResponse.model_validate(actor)


@router.put("/{actor_id}", response_model=VoiceActorResponse)
async def update_voice_actor(
    actor_id: int,
    actor_in: VoiceActorUpdate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """성우 정보 수정"""
    voice_actor_service = VoiceActorService()
    actor = await voice_actor_service.get_or_404(db, actor_id)
    updated_actor = await voice_actor_service.update(
        db,
        db_obj=actor,
        obj_in=actor_in.model_dump(exclude_unset=True)
    )
    return VoiceActorResponse.model_validate(updated_actor)


@router.post("/{actor_id}/activate", response_model=VoiceActorResponse)
async def activate_voice_actor(
    actor_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """성우 활성화"""
    voice_actor_service = VoiceActorService()
    actor = await voice_actor_service.activate_voice_actor(db, actor_id)
    return VoiceActorResponse.model_validate(actor)


@router.post("/{actor_id}/deactivate", response_model=VoiceActorResponse)
async def deactivate_voice_actor(
    actor_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """성우 비활성화"""
    voice_actor_service = VoiceActorService()
    actor = await voice_actor_service.deactivate_voice_actor(db, actor_id)
    return VoiceActorResponse.model_validate(actor)


# 음성 샘플 관리
@router.get("/{actor_id}/samples", response_model=list[VoiceSampleResponse])
async def get_voice_samples(
    actor_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """성우 음성 샘플 목록"""
    voice_sample_service = VoiceSampleService()
    samples = await voice_sample_service.get_samples_by_actor(db, actor_id)
    return [VoiceSampleResponse.model_validate(sample) for sample in samples]


@router.post("/{actor_id}/samples", response_model=VoiceSampleResponse, status_code=status.HTTP_201_CREATED)
async def upload_voice_sample(
    actor_id: int,
    text_content: str = Form(..., description="텍스트 내용"),
    audio_file: UploadFile = File(..., description="음성 파일"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """음성 샘플 업로드"""
    # 파일 확장자 검증
    if not validate_file_extension(audio_file.filename, settings.ALLOWED_FILE_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 파일 형식입니다."
        )
    
    # 파일 크기 확인
    if audio_file.size and audio_file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기가 너무 큽니다."
        )
    
    # 파일 저장
    audio_file_path = await save_upload_file(
        audio_file,
        directory=settings.AUDIO_DIR
    )
    
    # 샘플 생성
    sample_in = VoiceSampleCreate(
        voice_actor_id=actor_id,
        text_content=text_content
    )
    
    voice_sample_service = VoiceSampleService()
    sample = await voice_sample_service.create_voice_sample(
        db,
        sample_in=sample_in,
        audio_file_path=audio_file_path,
        file_size=audio_file.size,
        uploaded_by=current_user.id
    )
    
    return VoiceSampleResponse.model_validate(sample)


@router.delete("/{actor_id}/samples/{sample_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_sample(
    actor_id: int,
    sample_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """음성 샘플 삭제"""
    voice_sample_service = VoiceSampleService()
    await voice_sample_service.delete(db, id=sample_id)


# 음성 모델 관리
@router.get("/{actor_id}/models", response_model=list[VoiceModelResponse])
async def get_voice_models(
    actor_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """성우 음성 모델 목록"""
    voice_model_service = VoiceModelService()
    models = await voice_model_service.get_models_by_actor(db, actor_id)
    return [VoiceModelResponse.model_validate(model) for model in models]


@router.post("/{actor_id}/models", response_model=VoiceModelResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_model(
    actor_id: int,
    model_in: VoiceModelCreate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """새 음성 모델 생성"""
    # actor_id를 모델 생성 데이터에 설정
    model_data = model_in.model_dump()
    model_data["voice_actor_id"] = actor_id
    
    voice_model_service = VoiceModelService()
    model = await voice_model_service.create_voice_model(
        db,
        model_in=VoiceModelCreate(**model_data)
    )
    return VoiceModelResponse.model_validate(model)
