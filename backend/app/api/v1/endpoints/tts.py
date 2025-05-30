# app/api/v1/endpoints/tts.py
"""
TTS 관리 엔드포인트
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_operator_user
from app.api.dependencies.database import get_async_session
from app.api.dependencies.pagination import PaginationParams, SearchParams
from app.models.user import User
from app.schemas.tts import (
    TTSGenerationListResponse,
    TTSGenerationRequest,
    TTSGenerationResponse,
    TTSLibraryCreate,
    TTSLibraryResponse,
    TTSLibraryUpdate,
    TTSScriptCreate,
    TTSScriptResponse,
    TTSScriptUpdate,
)
from app.services.tts_service import TTSGenerationService, TTSLibraryService, TTSScriptService
from app.utils.constants import GenerationStatus

router = APIRouter()


# TTS 스크립트 관리
@router.get("/scripts", response_model=list[TTSScriptResponse])
async def get_tts_scripts(
    scenario_id: Optional[int] = Query(None, description="시나리오 ID 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 스크립트 목록 조회"""
    script_service = TTSScriptService()
    if scenario_id:
        scripts = await script_service.get_scripts_by_scenario(db, scenario_id)
    else:
        scripts = await script_service.get_multi(db)
    
    return [TTSScriptResponse.model_validate(script) for script in scripts]


@router.get("/scripts/{script_id}", response_model=TTSScriptResponse)
async def get_tts_script(
    script_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """특정 TTS 스크립트 조회"""
    script_service = TTSScriptService()
    script = await script_service.get_or_404(db, script_id)
    return TTSScriptResponse.model_validate(script)


@router.post("/scripts", response_model=TTSScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_tts_script(
    script_in: TTSScriptCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """새 TTS 스크립트 생성"""
    script_service = TTSScriptService()
    script = await script_service.create_tts_script(
        db,
        script_in=script_in,
        created_by=current_user.id
    )
    return TTSScriptResponse.model_validate(script)


@router.put("/scripts/{script_id}", response_model=TTSScriptResponse)
async def update_tts_script(
    script_id: int,
    script_in: TTSScriptUpdate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """TTS 스크립트 수정"""
    script_service = TTSScriptService()
    script = await script_service.get_or_404(db, script_id)
    updated_script = await script_service.update(
        db,
        db_obj=script,
        obj_in=script_in.model_dump(exclude_unset=True)
    )
    return TTSScriptResponse.model_validate(updated_script)


@router.delete("/scripts/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tts_script(
    script_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """TTS 스크립트 삭제"""
    script_service = TTSScriptService()
    await script_service.delete(db, id=script_id)


# TTS 생성 관리
@router.post("/scripts/{script_id}/generate", response_model=TTSGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_tts(
    script_id: int,
    generation_request: TTSGenerationRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """TTS 생성 요청"""
    generation_service = TTSGenerationService()
    generation = await generation_service.create_tts_generation(
        db,
        script_id=script_id,
        generation_request=generation_request,
        requested_by=current_user.id
    )
    return TTSGenerationResponse.model_validate(generation)


@router.get("/generations", response_model=TTSGenerationListResponse)
async def get_tts_generations(
    pagination: PaginationParams = Depends(),
    status_filter: Optional[GenerationStatus] = Query(None, description="상태 필터"),
    requested_by: Optional[int] = Query(None, description="요청자 필터"),
    voice_model_id: Optional[int] = Query(None, description="음성 모델 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 생성 목록 조회"""
    generation_service = TTSGenerationService()
    filters = {}
    if status_filter:
        filters["status"] = status_filter
    if requested_by:
        filters["requested_by"] = requested_by
    if voice_model_id:
        filters["voice_model_id"] = voice_model_id
    
    generations = await generation_service.get_multi(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        filters=filters
    )
    
    total = await generation_service.count(db, filters=filters)
    
    return TTSGenerationListResponse(
        items=[TTSGenerationResponse.model_validate(gen) for gen in generations],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.get("/generations/{generation_id}", response_model=TTSGenerationResponse)
async def get_tts_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 생성 상태 조회"""
    generation_service = TTSGenerationService()
    generation = await generation_service.get_or_404(db, generation_id)
    return TTSGenerationResponse.model_validate(generation)


@router.get("/generations/{generation_id}/download")
async def download_tts_audio(
    generation_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 오디오 파일 다운로드"""
    generation_service = TTSGenerationService()
    generation = await generation_service.get_or_404(db, generation_id)
    
    if generation.status != GenerationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TTS 생성이 완료되지 않았습니다."
        )
    
    if not generation.audio_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="오디오 파일을 찾을 수 없습니다."
        )
    
    return FileResponse(
        generation.audio_file_path,
        media_type="audio/wav",
        filename=f"tts_{generation_id}.wav"
    )


@router.delete("/generations/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_tts_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """TTS 생성 취소"""
    generation_service = TTSGenerationService()
    generation = await generation_service.get_or_404(db, generation_id)
    
    if generation.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 완료되거나 실패한 작업은 취소할 수 없습니다."
        )
    
    await generation_service.update_generation_status(
        db,
        generation_id,
        GenerationStatus.CANCELLED
    )


# TTS 라이브러리 관리
@router.get("/library", response_model=list[TTSLibraryResponse])
async def get_tts_library(
    pagination: PaginationParams = Depends(),
    search: SearchParams = Depends(),
    tags: Optional[str] = Query(None, description="태그 필터"),
    voice_actor_id: Optional[int] = Query(None, description="성우 필터"),
    is_public: Optional[bool] = Query(None, description="공개 여부 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 라이브러리 조회"""
    library_service = TTSLibraryService()
    items, total = await library_service.search_library(
        db,
        search=search.search,
        category=search.category,
        tags=tags,
        voice_actor_id=voice_actor_id,
        is_public=is_public,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return [TTSLibraryResponse.model_validate(item) for item in items]


@router.post("/library", response_model=TTSLibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_library_item(
    library_in: TTSLibraryCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """TTS 라이브러리 아이템 생성"""
    library_service = TTSLibraryService()
    item = await library_service.create_library_item(
        db,
        library_in=library_in,
        created_by=current_user.id
    )
    return TTSLibraryResponse.model_validate(item)


@router.put("/library/{item_id}", response_model=TTSLibraryResponse)
async def update_library_item(
    item_id: int,
    library_in: TTSLibraryUpdate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """TTS 라이브러리 아이템 수정"""
    library_service = TTSLibraryService()
    item = await library_service.get_or_404(db, item_id)
    updated_item = await library_service.update(
        db,
        db_obj=item,
        obj_in=library_in.model_dump(exclude_unset=True)
    )
    return TTSLibraryResponse.model_validate(updated_item)


@router.post("/library/{item_id}/use", response_model=TTSLibraryResponse)
async def use_library_item(
    item_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """TTS 라이브러리 아이템 사용 (사용 횟수 증가)"""
    library_service = TTSLibraryService()
    item = await library_service.increment_usage_count(db, item_id)
    return TTSLibraryResponse.model_validate(item)


@router.delete("/library/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library_item(
    item_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """TTS 라이브러리 아이템 삭제"""
    library_service = TTSLibraryService()
    await library_service.delete(db, id=item_id)
