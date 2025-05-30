# app/api/v1/endpoints/scenarios.py
"""
시나리오 관리 엔드포인트
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_operator_user
from app.api.dependencies.database import get_async_session
from app.api.dependencies.pagination import PaginationParams, SearchParams
from app.models.user import User
from app.schemas.scenario import (
    ScenarioConnectionCreate,
    ScenarioConnectionResponse,
    ScenarioConnectionUpdate,
    ScenarioCreate,
    ScenarioDetailResponse,
    ScenarioListResponse,
    ScenarioNodeCreate,
    ScenarioNodeResponse,
    ScenarioNodeUpdate,
    ScenarioResponse,
    ScenarioUpdate,
)
from app.services.scenario_service import (
    ScenarioConnectionService,
    ScenarioNodeService,
    ScenarioService,
)
from app.utils.constants import ScenarioStatus

router = APIRouter()


# 시나리오 관리
@router.get("/", response_model=ScenarioListResponse)
async def get_scenarios(
    pagination: PaginationParams = Depends(),
    search: SearchParams = Depends(),
    status_filter: Optional[ScenarioStatus] = Query(None, description="상태 필터"),
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시나리오 목록 조회"""
    scenario_service = ScenarioService()
    scenarios, total = await scenario_service.search_scenarios(
        db,
        search=search.search,
        category=search.category,
        status=status_filter,
        created_by=search.created_by,
        skip=pagination.skip,
        limit=pagination.limit
    )
    
    return ScenarioListResponse(
        items=[ScenarioResponse.model_validate(scenario) for scenario in scenarios],
        page=pagination.page,
        size=pagination.size,
        total=total,
        pages=(total + pagination.size - 1) // pagination.size
    )


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시나리오 상세 조회"""
    scenario_service = ScenarioService()
    scenario = await scenario_service.get_scenario_with_details(db, scenario_id)
    return ScenarioDetailResponse.model_validate(scenario)


@router.post("/", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_in: ScenarioCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """새 시나리오 생성"""
    scenario_service = ScenarioService()
    scenario = await scenario_service.create_scenario(
        db, 
        scenario_in=scenario_in, 
        created_by=current_user.id
    )
    return ScenarioResponse.model_validate(scenario)


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    scenario_in: ScenarioUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """시나리오 수정"""
    scenario_service = ScenarioService()
    scenario = await scenario_service.update_scenario(
        db,
        scenario_id=scenario_id,
        scenario_in=scenario_in,
        updated_by=current_user.id
    )
    return ScenarioResponse.model_validate(scenario)


@router.post("/{scenario_id}/deploy", response_model=ScenarioResponse)
async def deploy_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """시나리오 배포"""
    scenario_service = ScenarioService()
    scenario = await scenario_service.deploy_scenario(
        db, 
        scenario_id, 
        deployed_by=current_user.id
    )
    return ScenarioResponse.model_validate(scenario)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 삭제"""
    scenario_service = ScenarioService()
    await scenario_service.delete(db, id=scenario_id)


# 시나리오 노드 관리
@router.get("/{scenario_id}/nodes", response_model=list[ScenarioNodeResponse])
async def get_scenario_nodes(
    scenario_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시나리오 노드 목록 조회"""
    node_service = ScenarioNodeService()
    nodes = await node_service.get_scenario_nodes(db, scenario_id)
    return [ScenarioNodeResponse.model_validate(node) for node in nodes]


@router.post("/{scenario_id}/nodes", response_model=ScenarioNodeResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario_node(
    scenario_id: int,
    node_in: ScenarioNodeCreate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 노드 생성"""
    node_service = ScenarioNodeService()
    node = await node_service.create_node(
        db,
        scenario_id=scenario_id,
        node_in=node_in
    )
    return ScenarioNodeResponse.model_validate(node)


@router.put("/{scenario_id}/nodes/{node_id}", response_model=ScenarioNodeResponse)
async def update_scenario_node(
    scenario_id: int,
    node_id: int,
    node_in: ScenarioNodeUpdate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 노드 수정"""
    node_service = ScenarioNodeService()
    node = await node_service.update_node(
        db,
        node_id=node_id,
        node_in=node_in
    )
    return ScenarioNodeResponse.model_validate(node)


@router.delete("/{scenario_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario_node(
    scenario_id: int,
    node_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 노드 삭제"""
    node_service = ScenarioNodeService()
    await node_service.delete(db, id=node_id)


# 시나리오 연결 관리
@router.get("/{scenario_id}/connections", response_model=list[ScenarioConnectionResponse])
async def get_scenario_connections(
    scenario_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시나리오 연결 목록 조회"""
    connection_service = ScenarioConnectionService()
    connections = await connection_service.get_scenario_connections(db, scenario_id)
    return [ScenarioConnectionResponse.model_validate(conn) for conn in connections]


@router.post("/{scenario_id}/connections", response_model=ScenarioConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario_connection(
    scenario_id: int,
    connection_in: ScenarioConnectionCreate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 연결 생성"""
    connection_service = ScenarioConnectionService()
    connection = await connection_service.create_connection(
        db,
        scenario_id=scenario_id,
        connection_in=connection_in
    )
    return ScenarioConnectionResponse.model_validate(connection)


@router.put("/{scenario_id}/connections/{connection_id}", response_model=ScenarioConnectionResponse)
async def update_scenario_connection(
    scenario_id: int,
    connection_id: int,
    connection_in: ScenarioConnectionUpdate,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 연결 수정"""
    connection_service = ScenarioConnectionService()
    connection = await connection_service.update(
        db,
        db_obj=await connection_service.get_or_404(db, connection_id),
        obj_in=connection_in.model_dump(exclude_unset=True)
    )
    return ScenarioConnectionResponse.model_validate(connection)


@router.delete("/{scenario_id}/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario_connection(
    scenario_id: int,
    connection_id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시나리오 연결 삭제"""
    connection_service = ScenarioConnectionService()
    await connection_service.delete(db, id=connection_id)
