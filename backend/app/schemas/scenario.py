"""
시나리오 관련 스키마
"""
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema, IDMixin, PaginationSchema, TimestampMixin
from app.utils.constants import NodeType, ScenarioStatus


class ScenarioBase(BaseSchema):
    """시나리오 기본 스키마"""
    
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    version: str = Field(default="1.0", max_length=20)
    is_template: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScenarioCreate(ScenarioBase):
    """시나리오 생성 스키마"""
    pass


class ScenarioUpdate(BaseSchema):
    """시나리오 수정 스키마"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class ScenarioResponse(IDMixin, TimestampMixin, ScenarioBase):
    """시나리오 응답 스키마"""
    
    status: ScenarioStatus
    deployed_at: Optional[str] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None


class ScenarioListResponse(PaginationSchema):
    """시나리오 목록 응답 스키마"""
    
    items: List[ScenarioResponse]


# 시나리오 노드 스키마
class ScenarioNodeBase(BaseSchema):
    """시나리오 노드 기본 스키마"""
    
    node_id: str = Field(..., min_length=1, max_length=50)
    node_type: NodeType
    name: str = Field(..., min_length=1, max_length=200)
    position_x: int = 0
    position_y: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)


class ScenarioNodeCreate(ScenarioNodeBase):
    """시나리오 노드 생성 스키마"""
    pass


class ScenarioNodeUpdate(BaseSchema):
    """시나리오 노드 수정 스키마"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class ScenarioNodeResponse(IDMixin, TimestampMixin, ScenarioNodeBase):
    """시나리오 노드 응답 스키마"""
    
    scenario_id: int


# 시나리오 연결 스키마
class ScenarioConnectionBase(BaseSchema):
    """시나리오 연결 기본 스키마"""
    
    source_node_id: str = Field(..., min_length=1, max_length=50)
    target_node_id: str = Field(..., min_length=1, max_length=50)
    condition: Optional[Dict[str, Any]] = None
    label: Optional[str] = Field(None, max_length=100)


class ScenarioConnectionCreate(ScenarioConnectionBase):
    """시나리오 연결 생성 스키마"""
    pass


class ScenarioConnectionUpdate(BaseSchema):
    """시나리오 연결 수정 스키마"""
    
    condition: Optional[Dict[str, Any]] = None
    label: Optional[str] = Field(None, max_length=100)


class ScenarioConnectionResponse(IDMixin, TimestampMixin, ScenarioConnectionBase):
    """시나리오 연결 응답 스키마"""
    
    scenario_id: int


class ScenarioDetailResponse(ScenarioResponse):
    """시나리오 상세 응답 스키마"""
    
    nodes: List[ScenarioNodeResponse] = Field(default_factory=list)
    connections: List[ScenarioConnectionResponse] = Field(default_factory=list)
