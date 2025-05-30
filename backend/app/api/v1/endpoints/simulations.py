# app/api/v1/endpoints/simulations.py
"""
시나리오 시뮬레이션 엔드포인트
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_active_user, get_operator_user
from app.api.dependencies.database import get_async_session
from app.models.user import User
from app.schemas.simulation import (
    SimulationActionRequest,
    SimulationCreateRequest,
    SimulationResponse,
    SimulationStatusResponse,
)
from app.services.simulation_service import SimulationService

router = APIRouter()


@router.post("/scenarios/{scenario_id}/simulate", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def start_simulation(
    scenario_id: int,
    simulation_request: SimulationCreateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_operator_user)
):
    """시나리오 시뮬레이션 시작"""
    simulation_service = SimulationService()
    simulation = await simulation_service.start_simulation(
        db,
        scenario_id=scenario_id,
        start_node_id=simulation_request.start_node_id,
        config=simulation_request.simulation_config,
        created_by=current_user.id
    )
    return SimulationResponse.model_validate(simulation)


@router.get("/{simulation_id}/status", response_model=SimulationStatusResponse)
async def get_simulation_status(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 상태 조회"""
    simulation_service = SimulationService()
    simulation = await simulation_service.get_simulation_status(db, simulation_id)
    return SimulationStatusResponse.model_validate(simulation)


@router.post("/{simulation_id}/action", response_model=SimulationResponse)
async def execute_simulation_action(
    simulation_id: str,
    action_request: SimulationActionRequest,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 액션 실행"""
    simulation_service = SimulationService()
    
    # 시뮬레이션 상태 확인
    simulation = await simulation_service.get_simulation_by_id(db, simulation_id)
    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시뮬레이션을 찾을 수 없습니다."
        )
    
    if simulation.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="시뮬레이션이 활성 상태가 아닙니다."
        )
    
    # 액션 실행
    updated_simulation = await simulation_service.execute_action(
        db,
        simulation_id=simulation_id,
        action_type=action_request.action_type,
        value=action_request.value,
        additional_data=action_request.additional_data
    )
    
    return SimulationResponse.model_validate(updated_simulation)


@router.post("/{simulation_id}/reset", response_model=SimulationResponse)
async def reset_simulation(
    simulation_id: str,
    start_node_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시뮬레이션 리셋"""
    simulation_service = SimulationService()
    simulation = await simulation_service.reset_simulation(
        db,
        simulation_id=simulation_id,
        start_node_id=start_node_id
    )
    return SimulationResponse.model_validate(simulation)


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_simulation(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 종료"""
    simulation_service = SimulationService()
    await simulation_service.stop_simulation(db, simulation_id)


@router.get("/{simulation_id}/history")
async def get_simulation_history(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 실행 이력 조회"""
    simulation_service = SimulationService()
    history = await simulation_service.get_simulation_history(db, simulation_id)
    return {
        "simulation_id": simulation_id,
        "steps": history["steps"],
        "total_steps": len(history["steps"]),
        "current_step": history["current_step"],
        "execution_time": history["execution_time"],
        "errors": history["errors"]
    }


@router.get("/{simulation_id}/export")
async def export_simulation_results(
    simulation_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 결과 내보내기"""
    simulation_service = SimulationService()
    
    if format not in ["json", "csv", "xlsx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 형식입니다. (json, csv, xlsx)"
        )
    
    export_data = await simulation_service.export_simulation_results(
        db,
        simulation_id=simulation_id,
        format=format
    )
    
    return {
        "simulation_id": simulation_id,
        "format": format,
        "data": export_data["content"],
        "metadata": export_data["metadata"],
        "generated_at": export_data["generated_at"]
    }


@router.post("/{simulation_id}/playback", response_model=SimulationResponse)
async def playback_simulation(
    simulation_id: str,
    speed: float = 1.0,
    auto_advance: bool = True,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 재생 (자동 실행)"""
    if speed <= 0 or speed > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="재생 속도는 0.1에서 10 사이여야 합니다."
        )
    
    simulation_service = SimulationService()
    simulation = await simulation_service.start_playback(
        db,
        simulation_id=simulation_id,
        speed=speed,
        auto_advance=auto_advance
    )
    
    return SimulationResponse.model_validate(simulation)


@router.post("/{simulation_id}/pause")
async def pause_simulation(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 일시정지"""
    simulation_service = SimulationService()
    await simulation_service.pause_simulation(db, simulation_id)
    return {"message": "시뮬레이션이 일시정지되었습니다."}


@router.post("/{simulation_id}/resume")
async def resume_simulation(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 재개"""
    simulation_service = SimulationService()
    await simulation_service.resume_simulation(db, simulation_id)
    return {"message": "시뮬레이션이 재개되었습니다."}


@router.get("/{simulation_id}/debug")
async def get_simulation_debug_info(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_operator_user)
):
    """시뮬레이션 디버그 정보 조회"""
    simulation_service = SimulationService()
    debug_info = await simulation_service.get_debug_info(db, simulation_id)
    return {
        "simulation_id": simulation_id,
        "current_state": debug_info["current_state"],
        "variables": debug_info["variables"],
        "call_stack": debug_info["call_stack"],
        "performance_metrics": debug_info["performance_metrics"],
        "memory_usage": debug_info["memory_usage"],
        "execution_trace": debug_info["execution_trace"]
    }


@router.post("/{simulation_id}/validate")
async def validate_simulation(
    simulation_id: str,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_active_user)
):
    """시뮬레이션 유효성 검증"""
    simulation_service = SimulationService()
    validation_result = await simulation_service.validate_simulation(db, simulation_id)
    return {
        "simulation_id": simulation_id,
        "is_valid": validation_result["is_valid"],
        "errors": validation_result["errors"],
        "warnings": validation_result["warnings"],
        "recommendations": validation_result["recommendations"],
        "coverage": validation_result["coverage"]
    }
