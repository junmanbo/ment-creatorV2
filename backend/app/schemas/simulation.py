# app/schemas/simulation.py
"""
시뮬레이션 관련 스키마
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.utils.constants import NodeType


class SimulationConfig(BaseModel):
    """시뮬레이션 설정"""
    timeout: Optional[int] = Field(default=300, description="타임아웃 (초)")
    log_level: Optional[str] = Field(default="info", description="로그 레벨")
    auto_advance: Optional[bool] = Field(default=False, description="자동 진행")
    speed: Optional[float] = Field(default=1.0, description="실행 속도")


class SimulationCreateRequest(BaseModel):
    """시뮬레이션 생성 요청"""
    start_node_id: Optional[str] = Field(None, description="시작 노드 ID")
    simulation_config: Optional[SimulationConfig] = Field(default_factory=SimulationConfig, description="시뮬레이션 설정")


class SimulationActionRequest(BaseModel):
    """시뮬레이션 액션 요청"""
    action_type: str = Field(..., description="액션 타입")
    value: Optional[Any] = Field(None, description="액션 값")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="추가 데이터")


class SimulationNodeState(BaseModel):
    """시뮬레이션 노드 상태"""
    node_id: str = Field(..., description="노드 ID")
    node_type: Optional[NodeType] = Field(None, description="노드 타입")
    name: Optional[str] = Field(None, description="노드 이름")
    config: Dict[str, Any] = Field(default_factory=dict, description="노드 설정")


class SimulationAction(BaseModel):
    """시뮬레이션 액션"""
    type: str = Field(..., description="액션 타입")
    label: str = Field(..., description="액션 라벨")
    key: Optional[str] = Field(None, description="액션 키")
    input_type: Optional[str] = Field(None, description="입력 타입")


class SimulationResponse(BaseModel):
    """시뮬레이션 응답"""
    simulation_id: str = Field(..., description="시뮬레이션 ID")
    scenario_id: Optional[int] = Field(None, description="시나리오 ID")
    current_node: SimulationNodeState = Field(..., description="현재 노드")
    available_actions: List[SimulationAction] = Field(default_factory=list, description="사용 가능한 액션들")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="세션 데이터")
    status: str = Field(..., description="시뮬레이션 상태")
    execution_time: float = Field(..., description="실행 시간 (초)")


class SimulationStatusResponse(BaseModel):
    """시뮬레이션 상태 응답"""
    simulation_id: str = Field(..., description="시뮬레이션 ID")
    status: str = Field(..., description="시뮬레이션 상태")
    current_node: SimulationNodeState = Field(..., description="현재 노드")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="세션 데이터")
    execution_time: float = Field(..., description="실행 시간 (초)")


class SimulationHistoryStep(BaseModel):
    """시뮬레이션 실행 단계"""
    timestamp: float = Field(..., description="타임스탬프")
    node_id: str = Field(..., description="노드 ID")
    action_type: str = Field(..., description="액션 타입")
    value: Optional[Any] = Field(None, description="액션 값")
    additional_data: Dict[str, Any] = Field(default_factory=dict, description="추가 데이터")


class SimulationHistory(BaseModel):
    """시뮬레이션 실행 이력"""
    simulation_id: str = Field(..., description="시뮬레이션 ID")
    steps: List[SimulationHistoryStep] = Field(default_factory=list, description="실행 단계들")
    total_steps: int = Field(..., description="총 단계 수")
    current_step: int = Field(..., description="현재 단계")
    execution_time: float = Field(..., description="총 실행 시간")
    errors: List[str] = Field(default_factory=list, description="오류 목록")


class SimulationExportRequest(BaseModel):
    """시뮬레이션 내보내기 요청"""
    format: str = Field(default="json", description="내보내기 형식 (json, csv, xlsx)")
    include_metadata: bool = Field(default=True, description="메타데이터 포함 여부")


class SimulationExportResponse(BaseModel):
    """시뮬레이션 내보내기 응답"""
    simulation_id: str = Field(..., description="시뮬레이션 ID")
    format: str = Field(..., description="형식")
    data: Any = Field(..., description="내보낸 데이터")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    generated_at: datetime = Field(..., description="생성일시")


class SimulationValidationResult(BaseModel):
    """시뮬레이션 유효성 검증 결과"""
    simulation_id: str = Field(..., description="시뮬레이션 ID")
    is_valid: bool = Field(..., description="유효성 여부")
    errors: List[str] = Field(default_factory=list, description="오류 목록")
    warnings: List[str] = Field(default_factory=list, description="경고 목록")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")
    coverage: float = Field(..., description="커버리지 (%)") 


class SimulationDebugInfo(BaseModel):
    """시뮬레이션 디버그 정보"""
    simulation_id: str = Field(..., description="시뮬레이션 ID")
    current_state: Dict[str, Any] = Field(default_factory=dict, description="현재 상태")
    variables: Dict[str, Any] = Field(default_factory=dict, description="변수들")
    call_stack: List[Dict] = Field(default_factory=list, description="호출 스택")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="성능 메트릭")
    memory_usage: int = Field(..., description="메모리 사용량")
    execution_trace: List[Dict] = Field(default_factory=list, description="실행 추적")


class SimulationPlaybackRequest(BaseModel):
    """시뮬레이션 재생 요청"""
    speed: float = Field(default=1.0, ge=0.1, le=10.0, description="재생 속도")
    auto_advance: bool = Field(default=True, description="자동 진행")
