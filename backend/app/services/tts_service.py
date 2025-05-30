"""
TTS 서비스
"""

import asyncio
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.models.tts import TTSGeneration, TTSLibrary, TTSScript
from app.schemas.tts import (
    TTSGenerationRequest,
    TTSLibraryCreate,
    TTSScriptCreate,
)
from app.services.base import BaseService
from app.utils.constants import GenerationStatus, ModelStatus
from app.utils.logger import logger
from app.utils.validators import DataValidator


class TTSScriptService(BaseService[TTSScript]):
    """TTS 스크립트 서비스"""

    def __init__(self):
        super().__init__(TTSScript)

    async def create_tts_script(
        self, db: AsyncSession, *, script_in: TTSScriptCreate, created_by: int
    ) -> TTSScript:
        """TTS 스크립트 생성"""
        # 시나리오와 노드 존재 확인
        await self._validate_scenario_node(db, script_in.scenario_id, script_in.node_id)

        # 음성 설정 검증
        if script_in.voice_settings:
            DataValidator.validate_tts_settings(script_in.voice_settings)

        script_data = script_in.model_dump()
        script_data["created_by"] = created_by

        return await self.create(db, obj_in=script_data)

    async def get_scripts_by_scenario(
        self, db: AsyncSession, scenario_id: int
    ) -> list[TTSScript]:
        """시나리오별 스크립트 조회"""
        result = await db.execute(
            select(TTSScript)
            .where(TTSScript.scenario_id == scenario_id)
            .order_by(TTSScript.created_at)
        )
        return result.scalars().all()

    async def _validate_scenario_node(
        self, db: AsyncSession, scenario_id: int, node_id: str
    ) -> None:
        """시나리오 노드 존재 확인"""
        from app.models.scenario import ScenarioNode

        result = await db.execute(
            select(ScenarioNode).where(
                ScenarioNode.scenario_id == scenario_id, ScenarioNode.node_id == node_id
            )
        )

        if not result.scalars().first():
            raise ValidationError(f"시나리오 노드를 찾을 수 없습니다: {node_id}")


class TTSGenerationService(BaseService[TTSGeneration]):
    """TTS 생성 서비스"""

    def __init__(self):
        super().__init__(TTSGeneration)

    async def create_tts_generation(
        self,
        db: AsyncSession,
        *,
        script_id: int,
        generation_request: TTSGenerationRequest,
        requested_by: int,
    ) -> TTSGeneration:
        """TTS 생성 요청"""
        # 스크립트 존재 확인
        script_service = TTSScriptService()
        await script_service.get_or_404(db, script_id)

        # 음성 모델 존재 확인
        from app.services.voice_service import VoiceModelService

        model_service = VoiceModelService()
        voice_model = await model_service.get_or_404(
            db, generation_request.voice_model_id
        )

        if voice_model.status != ModelStatus.READY:
            raise ValidationError("선택한 음성 모델이 사용 가능한 상태가 아닙니다.")

        generation_data = {
            "script_id": script_id,
            "voice_model_id": generation_request.voice_model_id,
            "generation_params": generation_request.generation_params,
            "requested_by": requested_by,
            "status": GenerationStatus.PENDING,
        }

        generation = await self.create(db, obj_in=generation_data)

        # 비동기로 TTS 생성 시작
        task = asyncio.create_task(self._process_tts_generation(db, generation.id))
        # 태스크 참조 저장 (가비지 컬렉터 방지)
        generation._task = task

        return generation

    async def get_generations_by_status(
        self, db: AsyncSession, status: GenerationStatus
    ) -> list[TTSGeneration]:
        """상태별 생성 목록 조회"""
        result = await db.execute(
            select(TTSGeneration)
            .where(TTSGeneration.status == status)
            .order_by(TTSGeneration.created_at.desc())
        )
        return result.scalars().all()

    async def update_generation_status(
        self, db: AsyncSession, generation_id: int, status: GenerationStatus, **kwargs
    ) -> TTSGeneration:
        """생성 상태 업데이트"""
        generation = await self.get_or_404(db, generation_id)

        update_data = {"status": status}
        update_data.update(kwargs)

        return await self.update(db, db_obj=generation, obj_in=update_data)

    async def _process_tts_generation(
        self, db: AsyncSession, generation_id: int
    ) -> None:
        """TTS 생성 처리 (백그라운드 작업)"""
        try:
            # 상태를 처리 중으로 변경
            await self.update_generation_status(
                db,
                generation_id,
                GenerationStatus.PROCESSING,
                started_at=int(datetime.utcnow().timestamp()),
            )

            # 실제 TTS 생성 로직 (여기서는 시뮬레이션)
            # 실제로는 Voice Cloning 모델을 사용해서 음성 생성
            await asyncio.sleep(5)  # 생성 시간 시뮬레이션

            # 생성 완료
            audio_file_path = f"./audio_files/tts_{generation_id}.wav"

            await self.update_generation_status(
                db,
                generation_id,
                GenerationStatus.COMPLETED,
                audio_file_path=audio_file_path,
                file_size=1024000,  # 1MB
                duration=10.5,
                quality_score=92.3,
                completed_at=int(datetime.utcnow().timestamp()),
            )

            logger.info("TTS generation completed", generation_id=generation_id)

        except Exception as e:
            logger.error(f"TTS generation failed: {e}", generation_id=generation_id)

            await self.update_generation_status(
                db,
                generation_id,
                GenerationStatus.FAILED,
                error_message=str(e),
                completed_at=int(datetime.utcnow().timestamp()),
            )


class TTSLibraryService(BaseService[TTSLibrary]):
    """TTS 라이브러리 서비스"""

    def __init__(self):
        super().__init__(TTSLibrary)

    async def create_library_item(
        self, db: AsyncSession, *, library_in: TTSLibraryCreate, created_by: int
    ) -> TTSLibrary:
        """라이브러리 아이템 생성"""
        library_data = library_in.model_dump()
        library_data["created_by"] = created_by

        return await self.create(db, obj_in=library_data)

    async def search_library(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        category: str | None = None,
        tags: str | None = None,
        voice_actor_id: int | None = None,
        is_public: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TTSLibrary], int]:
        """라이브러리 검색"""
        query = select(TTSLibrary)
        count_query = select(func.count(TTSLibrary.id))

        # 검색 조건 적용
        conditions = []

        if search:
            conditions.append(
                or_(
                    TTSLibrary.name.ilike(f"%{search}%"),
                    TTSLibrary.text_content.ilike(f"%{search}%"),
                )
            )

        if category:
            conditions.append(TTSLibrary.category == category)

        if tags:
            conditions.append(TTSLibrary.tags.ilike(f"%{tags}%"))

        if voice_actor_id:
            conditions.append(TTSLibrary.voice_actor_id == voice_actor_id)

        if is_public is not None:
            conditions.append(TTSLibrary.is_public == is_public)

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # 정렬 및 페이징
        query = query.order_by(TTSLibrary.usage_count.desc()).offset(skip).limit(limit)

        # 실행
        items_result = await db.execute(query)
        count_result = await db.execute(count_query)

        items = items_result.scalars().all()
        total = count_result.scalar()

        return items, total

    async def increment_usage_count(
        self, db: AsyncSession, library_id: int
    ) -> TTSLibrary:
        """사용 횟수 증가"""
        library_item = await self.get_or_404(db, library_id)

        return await self.update(
            db,
            db_obj=library_item,
            obj_in={"usage_count": library_item.usage_count + 1},
        )
