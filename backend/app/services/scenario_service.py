"""
시나리오 서비스
"""
from datetime import datetime
from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.models.scenario import (
    Scenario,
    ScenarioConnection,
    ScenarioNode,
    ScenarioVersion,
)
from app.schemas.scenario import (
    ScenarioConnectionCreate,
    ScenarioCreate,
    ScenarioNodeCreate,
    ScenarioNodeUpdate,
    ScenarioUpdate,
)
from app.services.base import BaseService
from app.utils.constants import ScenarioStatus
from app.utils.validators import DataValidator


class ScenarioService(BaseService[Scenario]):
    """시나리오 서비스"""

    def __init__(self):
        super().__init__(Scenario)

    async def create_scenario(
        self, db: AsyncSession, *, scenario_in: ScenarioCreate, created_by: int
    ) -> Scenario:
        """시나리오 생성"""
        # 중복 이름 확인
        await self._check_duplicate_name(db, scenario_in.name, scenario_in.version)

        scenario_data = scenario_in.model_dump()
        scenario_data["created_by"] = created_by
        scenario_data["updated_by"] = created_by

        return await self.create(db, obj_in=scenario_data)

    async def update_scenario(
        self,
        db: AsyncSession,
        *,
        scenario_id: int,
        scenario_in: ScenarioUpdate,
        updated_by: int,
    ) -> Scenario:
        """시나리오 수정"""
        scenario = await self.get_or_404(db, scenario_id)

        update_data = scenario_in.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.update(db, db_obj=scenario, obj_in=update_data)

    async def get_scenario_with_details(
        self, db: AsyncSession, scenario_id: int
    ) -> Scenario:
        """시나리오 상세 정보 조회 (노드, 연결 포함)"""
        result = await db.execute(
            select(Scenario)
            .options(selectinload(Scenario.nodes), selectinload(Scenario.connections))
            .where(Scenario.id == scenario_id)
        )
        scenario = result.scalars().first()

        if not scenario:
            raise NotFoundError("시나리오를 찾을 수 없습니다.")

        return scenario

    async def search_scenarios(
        self,
        db: AsyncSession,
        *,
        search: str | None = None,
        category: str | None = None,
        status: ScenarioStatus | None = None,
        created_by: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[Scenario], int]:
        """시나리오 검색"""
        query = select(Scenario)
        count_query = select(func.count(Scenario.id))

        # 검색 조건 적용
        conditions = []

        if search:
            conditions.append(
                or_(
                    Scenario.name.ilike(f"%{search}%"),
                    Scenario.description.ilike(f"%{search}%"),
                )
            )

        if category:
            conditions.append(Scenario.category == category)

        if status:
            conditions.append(Scenario.status == status)

        if created_by:
            conditions.append(Scenario.created_by == created_by)

        if conditions:
            query = query.where(*conditions)
            count_query = count_query.where(*conditions)

        # 정렬 및 페이징
        query = query.order_by(Scenario.updated_at.desc()).offset(skip).limit(limit)

        # 실행
        scenarios_result = await db.execute(query)
        count_result = await db.execute(count_query)

        scenarios = scenarios_result.scalars().all()
        total = count_result.scalar()

        return scenarios, total

    async def deploy_scenario(
        self, db: AsyncSession, scenario_id: int, deployed_by: int
    ) -> Scenario:
        """시나리오 배포"""
        scenario = await self.get_or_404(db, scenario_id)

        # 배포 가능 상태 확인
        if scenario.status != ScenarioStatus.TESTING:
            raise ValidationError("테스트 완료된 시나리오만 배포할 수 있습니다.")

        # 스냅샷 생성
        await self._create_version_snapshot(db, scenario)

        # 상태 업데이트
        update_data = {
            "status": ScenarioStatus.ACTIVE,
            "deployed_at": datetime.utcnow(),
            "updated_by": deployed_by,
        }
        
        return await self.update(db, db_obj=scenario, obj_in=update_data)

    async def _check_duplicate_name(
        self,
        db: AsyncSession,
        name: str,
        version: str,
        exclude_id: int | None = None,
    ) -> None:
        """중복 이름 확인"""
        query = select(Scenario).where(
            Scenario.name == name, Scenario.version == version
        )

        if exclude_id:
            query = query.where(Scenario.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalars().first()

        if existing:
            raise ValidationError(
                f"동일한 이름과 버전의 시나리오가 이미 존재합니다: {name} v{version}"
            )

    async def _create_version_snapshot(
        self, db: AsyncSession, scenario: Scenario
    ) -> ScenarioVersion:
        """버전 스냅샷 생성"""
        # 시나리오 전체 데이터 스냅샷
        snapshot = {
            "scenario": {
                "name": scenario.name,
                "description": scenario.description,
                "category": scenario.category,
                "metadata": scenario.meta_data,
            },
            "nodes": [],
            "connections": [],
        }

        version_data = {
            "scenario_id": scenario.id,
            "version": scenario.version,
            "snapshot": snapshot,
            "created_by": scenario.updated_by,
            "notes": f"v{scenario.version} 배포",
        }

        version = ScenarioVersion(**version_data)
        db.add(version)
        await db.commit()

        return version


class ScenarioNodeService(BaseService[ScenarioNode]):
    """시나리오 노드 서비스"""

    def __init__(self):
        super().__init__(ScenarioNode)

    async def create_node(
        self, db: AsyncSession, *, scenario_id: int, node_in: ScenarioNodeCreate
    ) -> ScenarioNode:
        """노드 생성"""
        # 노드 ID 중복 확인
        await self._check_duplicate_node_id(db, scenario_id, node_in.node_id)

        # 노드 설정 검증
        DataValidator.validate_scenario_node_config(node_in.node_type, node_in.config)

        node_data = node_in.model_dump()
        node_data["scenario_id"] = scenario_id

        return await self.create(db, obj_in=node_data)

    async def update_node(
        self, db: AsyncSession, *, node_id: int, node_in: ScenarioNodeUpdate
    ) -> ScenarioNode:
        """노드 수정"""
        node = await self.get_or_404(db, node_id)

        update_data = node_in.model_dump(exclude_unset=True)

        # 설정이 변경된 경우 검증
        if "config" in update_data:
            DataValidator.validate_scenario_node_config(
                node.node_type, update_data["config"]
            )

        return await self.update(db, db_obj=node, obj_in=update_data)

    async def get_scenario_nodes(
        self, db: AsyncSession, scenario_id: int
    ) -> List[ScenarioNode]:
        """시나리오의 모든 노드 조회"""
        result = await db.execute(
            select(ScenarioNode)
            .where(ScenarioNode.scenario_id == scenario_id)
            .order_by(ScenarioNode.created_at)
        )
        return result.scalars().all()

    async def _check_duplicate_node_id(
        self,
        db: AsyncSession,
        scenario_id: int,
        node_id: str,
        exclude_id: int | None = None,
    ) -> None:
        """노드 ID 중복 확인"""
        query = select(ScenarioNode).where(
            ScenarioNode.scenario_id == scenario_id, ScenarioNode.node_id == node_id
        )

        if exclude_id:
            query = query.where(ScenarioNode.id != exclude_id)

        result = await db.execute(query)
        existing = result.scalars().first()

        if existing:
            raise ValidationError(f"동일한 노드 ID가 이미 존재합니다: {node_id}")


class ScenarioConnectionService(BaseService[ScenarioConnection]):
    """시나리오 연결 서비스"""

    def __init__(self):
        super().__init__(ScenarioConnection)

    async def create_connection(
        self,
        db: AsyncSession,
        *,
        scenario_id: int,
        connection_in: ScenarioConnectionCreate,
    ) -> ScenarioConnection:
        """연결 생성"""
        # 노드 존재 확인
        await self._validate_nodes_exist(db, scenario_id, connection_in)

        connection_data = connection_in.model_dump()
        connection_data["scenario_id"] = scenario_id

        return await self.create(db, obj_in=connection_data)

    async def get_scenario_connections(
        self, db: AsyncSession, scenario_id: int
    ) -> List[ScenarioConnection]:
        """시나리오의 모든 연결 조회"""
        result = await db.execute(
            select(ScenarioConnection)
            .where(ScenarioConnection.scenario_id == scenario_id)
            .order_by(ScenarioConnection.created_at)
        )
        return result.scalars().all()

    async def _validate_nodes_exist(
        self,
        db: AsyncSession,
        scenario_id: int,
        connection_in: ScenarioConnectionCreate,
    ) -> None:
        """연결할 노드들이 존재하는지 확인"""
        # 출발 노드 확인
        source_result = await db.execute(
            select(ScenarioNode).where(
                ScenarioNode.scenario_id == scenario_id,
                ScenarioNode.node_id == connection_in.source_node_id,
            )
        )
        if not source_result.scalars().first():
            raise ValidationError(
                f"출발 노드를 찾을 수 없습니다: {connection_in.source_node_id}"
            )

        # 도착 노드 확인
        target_result = await db.execute(
            select(ScenarioNode).where(
                ScenarioNode.scenario_id == scenario_id,
                ScenarioNode.node_id == connection_in.target_node_id,
            )
        )
        if not target_result.scalars().first():
            raise ValidationError(
                f"도착 노드를 찾을 수 없습니다: {connection_in.target_node_id}"
            )
