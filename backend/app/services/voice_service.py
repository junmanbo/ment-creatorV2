"""
성우 및 음성 서비스
"""


from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_actor import VoiceActor, VoiceModel, VoiceSample
from app.schemas.voice_actor import (
    VoiceActorCreate,
    VoiceModelCreate,
    VoiceSampleCreate,
)
from app.services.base import BaseService
from app.utils.constants import AgeRangeType, GenderType, ModelStatus


class VoiceActorService(BaseService[VoiceActor]):
    """성우 서비스"""

    def __init__(self):
        super().__init__(VoiceActor)

    async def create_voice_actor(
        self, db: AsyncSession, *, voice_actor_in: VoiceActorCreate, created_by: int
    ) -> VoiceActor:
        """성우 생성"""
        voice_actor_data = voice_actor_in.model_dump()
        voice_actor_data["created_by"] = created_by

        return await self.create(db, obj_in=voice_actor_data)

    async def search_voice_actors(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        gender: GenderType | None = None,
        age_range: AgeRangeType | None = None,
        language: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[VoiceActor], int]:
        """성우 검색"""
        query = select(VoiceActor)
        count_query = select(func.count(VoiceActor.id))

        # 검색 조건 적용
        conditions = []

        if search:
            conditions.append(
                or_(
                    VoiceActor.name.ilike(f"%{search}%"),
                    VoiceActor.description.ilike(f"%{search}%"),
                )
            )

        if gender:
            conditions.append(VoiceActor.gender == gender)

        if age_range:
            conditions.append(VoiceActor.age_range == age_range)

        if language:
            conditions.append(VoiceActor.language == language)

        if is_active is not None:
            conditions.append(VoiceActor.is_active == is_active)

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # 정렬 및 페이징
        query = query.order_by(VoiceActor.created_at.desc()).offset(skip).limit(limit)

        # 실행
        actors_result = await db.execute(query)
        count_result = await db.execute(count_query)

        actors = actors_result.scalars().all()
        total = count_result.scalar()

        return actors, total

    async def activate_voice_actor(self, db: AsyncSession, actor_id: int) -> VoiceActor:
        """성우 활성화"""
        actor = await self.get_or_404(db, actor_id)
        return await self.update(db, db_obj=actor, obj_in={"is_active": True})

    async def deactivate_voice_actor(
        self, db: AsyncSession, actor_id: int
    ) -> VoiceActor:
        """성우 비활성화"""
        actor = await self.get_or_404(db, actor_id)
        return await self.update(db, db_obj=actor, obj_in={"is_active": False})


class VoiceModelService(BaseService[VoiceModel]):
    """음성 모델 서비스"""

    def __init__(self):
        super().__init__(VoiceModel)

    async def create_voice_model(
        self, db: AsyncSession, *, model_in: VoiceModelCreate
    ) -> VoiceModel:
        """음성 모델 생성"""
        # 성우 존재 확인
        voice_actor_service = VoiceActorService()
        await voice_actor_service.get_or_404(db, model_in.voice_actor_id)

        # 모델 경로 생성 (실제로는 파일 시스템에 저장)
        model_path = (
            f"./models/voice_actor_{model_in.voice_actor_id}_{model_in.model_name}"
        )

        model_data = model_in.model_dump()
        model_data["model_path"] = model_path

        return await self.create(db, obj_in=model_data)

    async def get_models_by_actor(
        self, db: AsyncSession, voice_actor_id: int
    ) -> list[VoiceModel]:
        """성우별 모델 조회"""
        result = await db.execute(
            select(VoiceModel)
            .where(VoiceModel.voice_actor_id == voice_actor_id)
            .order_by(VoiceModel.created_at.desc())
        )
        return result.scalars().all()

    async def get_ready_models(self, db: AsyncSession) -> list[VoiceModel]:
        """사용 가능한 모델 조회"""
        result = await db.execute(
            select(VoiceModel)
            .where(VoiceModel.status == ModelStatus.READY)
            .order_by(VoiceModel.quality_score.desc())
        )
        return result.scalars().all()

    async def update_model_status(
        self,
        db: AsyncSession,
        model_id: int,
        status: ModelStatus,
        quality_score: float | None = None,
    ) -> VoiceModel:
        """모델 상태 업데이트"""
        model = await self.get_or_404(db, model_id)

        update_data = {"status": status}
        if quality_score is not None:
            update_data["quality_score"] = quality_score

        return await self.update(db, db_obj=model, obj_in=update_data)


class VoiceSampleService(BaseService[VoiceSample]):
    """음성 샘플 서비스"""

    def __init__(self):
        super().__init__(VoiceSample)

    async def create_voice_sample(
        self,
        db: AsyncSession,
        *,
        sample_in: VoiceSampleCreate,
        audio_file_path: str,
        duration: float | None = None,
        sample_rate: int | None = None,
        file_size: int | None = None,
        uploaded_by: int,
    ) -> VoiceSample:
        """음성 샘플 생성"""
        # 성우 존재 확인
        voice_actor_service = VoiceActorService()
        await voice_actor_service.get_or_404(db, sample_in.voice_actor_id)

        sample_data = sample_in.model_dump()
        sample_data.update(
            {
                "audio_file_path": audio_file_path,
                "duration": duration,
                "sample_rate": sample_rate,
                "file_size": file_size,
                "uploaded_by": uploaded_by,
            }
        )

        return await self.create(db, obj_in=sample_data)

    async def get_samples_by_actor(
        self, db: AsyncSession, voice_actor_id: int
    ) -> list[VoiceSample]:
        """성우별 샘플 조회"""
        result = await db.execute(
            select(VoiceSample)
            .where(VoiceSample.voice_actor_id == voice_actor_id)
            .order_by(VoiceSample.created_at.desc())
        )
        return result.scalars().all()
