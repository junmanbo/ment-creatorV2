# app/services/simulation_service.py
"""
시뮬레이션 서비스
"""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, SimulationError, ValidationError
from app.models.scenario import Scenario, ScenarioNode, ScenarioConnection
from app.services.scenario_service import ScenarioService
from app.utils.constants import NodeType
from app.utils.logger import logger


class SimulationEngine:
    """시뮬레이션 엔진"""
    
    def __init__(self, scenario_data: Dict, config: Dict):
        self.scenario_data = scenario_data
        self.config = config
        self.current_node = None
        self.session_data = {}
        self.execution_history = []
        self.start_time = time.time()
        self.status = "idle"
        
    def start(self, start_node_id: str):
        """시뮬레이션 시작"""
        self.current_node = start_node_id
        self.status = "active"
        self.session_data = {}
        self.execution_history = []
        self.start_time = time.time()
        
        return self._get_current_state()
    
    def execute_action(self, action_type: str, value: Any = None, additional_data: Dict = None):
        """액션 실행"""
        if self.status != "active":
            raise SimulationError("시뮬레이션이 활성 상태가 아닙니다.")
        
        # 현재 노드 정보 가져오기
        current_node_data = self._get_node_data(self.current_node)
        if not current_node_data:
            raise SimulationError(f"노드를 찾을 수 없습니다: {self.current_node}")
        
        # 실행 이력 기록
        execution_step = {
            "timestamp": time.time(),
            "node_id": self.current_node,
            "action_type": action_type,
            "value": value,
            "additional_data": additional_data or {}
        }
        self.execution_history.append(execution_step)
        
        # 노드 타입에 따른 처리
        node_type = current_node_data.get("node_type")
        
        if node_type == NodeType.MESSAGE:
            return self._handle_message_node(current_node_data, action_type, value)
        elif node_type == NodeType.BRANCH:
            return self._handle_branch_node(current_node_data, action_type, value)
        elif node_type == NodeType.INPUT:
            return self._handle_input_node(current_node_data, action_type, value)
        elif node_type == NodeType.TRANSFER:
            return self._handle_transfer_node(current_node_data, action_type, value)
        elif node_type == NodeType.END:
            return self._handle_end_node(current_node_data, action_type, value)
        else:
            raise SimulationError(f"지원하지 않는 노드 타입: {node_type}")
    
    def _handle_message_node(self, node_data: Dict, action_type: str, value: Any):
        """메시지 노드 처리"""
        if action_type == "continue":
            # 다음 노드로 이동
            next_node = self._get_next_node(self.current_node)
            if next_node:
                self.current_node = next_node
            else:
                self.status = "completed"
        
        return self._get_current_state()
    
    def _handle_branch_node(self, node_data: Dict, action_type: str, value: Any):
        """분기 노드 처리"""
        if action_type == "select":
            config = node_data.get("config", {})
            branches = config.get("branches", [])
            
            # 선택된 분기 찾기
            selected_branch = None
            for branch in branches:
                if str(branch.get("key")) == str(value):
                    selected_branch = branch
                    break
            
            if selected_branch:
                target_node = selected_branch.get("target")
                if target_node:
                    self.current_node = target_node
                    self.session_data[f"branch_{self.current_node}_selection"] = value
            else:
                raise SimulationError(f"잘못된 분기 선택: {value}")
        
        return self._get_current_state()
    
    def _handle_input_node(self, node_data: Dict, action_type: str, value: Any):
        """입력 노드 처리"""
        if action_type == "input":
            # 입력값 검증 및 저장
            config = node_data.get("config", {})
            input_type = config.get("input_type", "text")
            
            if self._validate_input(value, input_type, config):
                self.session_data[f"input_{self.current_node}"] = value
                
                # 다음 노드로 이동
                next_node = self._get_next_node(self.current_node)
                if next_node:
                    self.current_node = next_node
                else:
                    self.status = "completed"
            else:
                raise SimulationError("잘못된 입력값입니다.")
        
        return self._get_current_state()
    
    def _handle_transfer_node(self, node_data: Dict, action_type: str, value: Any):
        """상담원 연결 노드 처리"""
        if action_type == "transfer":
            config = node_data.get("config", {})
            target = config.get("target", "general")
            
            self.session_data["transfer_target"] = target
            self.session_data["transfer_time"] = datetime.utcnow().isoformat()
            self.status = "transferred"
        
        return self._get_current_state()
    
    def _handle_end_node(self, node_data: Dict, action_type: str, value: Any):
        """종료 노드 처리"""
        self.status = "completed"
        self.session_data["completion_time"] = datetime.utcnow().isoformat()
        
        return self._get_current_state()
    
    def _get_node_data(self, node_id: str) -> Optional[Dict]:
        """노드 데이터 조회"""
        nodes = self.scenario_data.get("nodes", [])
        for node in nodes:
            if node.get("node_id") == node_id:
                return node
        return None
    
    def _get_next_node(self, current_node_id: str) -> Optional[str]:
        """다음 노드 찾기"""
        connections = self.scenario_data.get("connections", [])
        for connection in connections:
            if connection.get("source_node_id") == current_node_id:
                return connection.get("target_node_id")
        return None
    
    def _validate_input(self, value: Any, input_type: str, config: Dict) -> bool:
        """입력값 검증"""
        if input_type == "text":
            return isinstance(value, str) and len(value.strip()) > 0
        elif input_type == "number":
            try:
                float(value)
                return True
            except (ValueError, TypeError):
                return False
        elif input_type == "phone":
            # 간단한 전화번호 검증
            import re
            pattern = r"^\d{2,3}-\d{3,4}-\d{4}$"
            return bool(re.match(pattern, str(value)))
        else:
            return True
    
    def _get_current_state(self) -> Dict:
        """현재 상태 반환"""
        current_node_data = self._get_node_data(self.current_node)
        available_actions = self._get_available_actions(current_node_data)
        
        return {
            "current_node": {
                "node_id": self.current_node,
                "node_type": current_node_data.get("node_type") if current_node_data else None,
                "name": current_node_data.get("name") if current_node_data else None,
                "config": current_node_data.get("config", {}) if current_node_data else {}
            },
            "available_actions": available_actions,
            "session_data": self.session_data,
            "status": self.status,
            "execution_time": time.time() - self.start_time
        }
    
    def _get_available_actions(self, node_data: Optional[Dict]) -> List[Dict]:
        """사용 가능한 액션 목록"""
        if not node_data:
            return []
        
        node_type = node_data.get("node_type")
        config = node_data.get("config", {})
        
        if node_type == NodeType.MESSAGE:
            return [{"type": "continue", "label": "계속"}]
        elif node_type == NodeType.BRANCH:
            branches = config.get("branches", [])
            return [
                {
                    "type": "select",
                    "key": branch.get("key"),
                    "label": branch.get("label")
                }
                for branch in branches
            ]
        elif node_type == NodeType.INPUT:
            input_type = config.get("input_type", "text")
            return [
                {
                    "type": "input",
                    "input_type": input_type,
                    "label": config.get("prompt", "입력하세요")
                }
            ]
        elif node_type == NodeType.TRANSFER:
            return [{"type": "transfer", "label": "상담원 연결"}]
        elif node_type == NodeType.END:
            return [{"type": "end", "label": "종료"}]
        else:
            return []


class SimulationService:
    """시뮬레이션 서비스"""
    
    def __init__(self):
        self.active_simulations: Dict[str, SimulationEngine] = {}
        self.scenario_service = ScenarioService()
    
    async def start_simulation(
        self,
        db: AsyncSession,
        scenario_id: int,
        start_node_id: Optional[str] = None,
        config: Optional[Dict] = None,
        created_by: Optional[int] = None
    ) -> Dict:
        """시뮬레이션 시작"""
        # 시나리오 데이터 조회
        scenario_data = await self.scenario_service.get_scenario_with_details(db, scenario_id)
        
        if not scenario_data:
            raise NotFoundError("시나리오를 찾을 수 없습니다.")
        
        # 시작 노드 결정
        if not start_node_id:
            # 시작 노드 찾기
            start_nodes = [
                node for node in scenario_data.get("nodes", [])
                if node.get("node_type") == NodeType.START
            ]
            if start_nodes:
                start_node_id = start_nodes[0].get("node_id")
            else:
                raise ValidationError("시작 노드를 찾을 수 없습니다.")
        
        # 시뮬레이션 ID 생성
        simulation_id = str(uuid.uuid4())
        
        # 시뮬레이션 엔진 생성
        simulation_config = config or {}
        engine = SimulationEngine(scenario_data, simulation_config)
        
        # 시뮬레이션 시작
        initial_state = engine.start(start_node_id)
        
        # 활성 시뮬레이션에 추가
        self.active_simulations[simulation_id] = engine
        
        logger.info(
            "Simulation started",
            simulation_id=simulation_id,
            scenario_id=scenario_id,
            start_node_id=start_node_id
        )
        
        return {
            "simulation_id": simulation_id,
            "scenario_id": scenario_id,
            **initial_state
        }
    
    async def get_simulation_status(self, db: AsyncSession, simulation_id: str) -> Dict:
        """시뮬레이션 상태 조회"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        return {
            "simulation_id": simulation_id,
            **engine._get_current_state()
        }
    
    async def execute_action(
        self,
        db: AsyncSession,
        simulation_id: str,
        action_type: str,
        value: Any = None,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """액션 실행"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        try:
            result = engine.execute_action(action_type, value, additional_data)
            
            logger.info(
                "Simulation action executed",
                simulation_id=simulation_id,
                action_type=action_type,
                value=value
            )
            
            return {
                "simulation_id": simulation_id,
                **result
            }
        except Exception as e:
            logger.error(f"Simulation action failed: {e}")
            raise SimulationError(f"액션 실행에 실패했습니다: {str(e)}")
    
    async def reset_simulation(
        self,
        db: AsyncSession,
        simulation_id: str,
        start_node_id: Optional[str] = None
    ) -> Dict:
        """시뮬레이션 리셋"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        # 기존 시작 노드 또는 새로운 시작 노드 사용
        if not start_node_id:
            start_nodes = [
                node for node in engine.scenario_data.get("nodes", [])
                if node.get("node_type") == NodeType.START
            ]
            if start_nodes:
                start_node_id = start_nodes[0].get("node_id")
            else:
                raise ValidationError("시작 노드를 찾을 수 없습니다.")
        
        # 시뮬레이션 재시작
        result = engine.start(start_node_id)
        
        return {
            "simulation_id": simulation_id,
            **result
        }
    
    async def stop_simulation(self, db: AsyncSession, simulation_id: str) -> None:
        """시뮬레이션 종료"""
        if simulation_id in self.active_simulations:
            del self.active_simulations[simulation_id]
            logger.info(f"Simulation stopped: {simulation_id}")
    
    async def get_simulation_history(self, db: AsyncSession, simulation_id: str) -> Dict:
        """시뮬레이션 실행 이력"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        return {
            "steps": engine.execution_history,
            "current_step": len(engine.execution_history),
            "execution_time": time.time() - engine.start_time,
            "errors": []  # 에러 추적 기능 추가 가능
        }
    
    async def export_simulation_results(
        self,
        db: AsyncSession,
        simulation_id: str,
        format: str = "json"
    ) -> Dict:
        """시뮬레이션 결과 내보내기"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        export_data = {
            "simulation_id": simulation_id,
            "status": engine.status,
            "execution_history": engine.execution_history,
            "session_data": engine.session_data,
            "total_execution_time": time.time() - engine.start_time,
            "exported_at": datetime.utcnow().isoformat()
        }
        
        if format == "json":
            content = json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format == "csv":
            # CSV 형식으로 변환 (간단한 구현)
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 헤더
            writer.writerow(["Step", "Timestamp", "Node ID", "Action Type", "Value"])
            
            # 데이터
            for i, step in enumerate(engine.execution_history):
                writer.writerow([
                    i + 1,
                    step.get("timestamp"),
                    step.get("node_id"),
                    step.get("action_type"),
                    step.get("value")
                ])
            
            content = output.getvalue()
            output.close()
        else:
            content = str(export_data)
        
        return {
            "content": content,
            "metadata": {
                "format": format,
                "steps_count": len(engine.execution_history),
                "duration": time.time() - engine.start_time
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def get_simulation_by_id(self, db: AsyncSession, simulation_id: str) -> Optional[Dict]:
        """시뮬레이션 정보 조회"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            return None
        
        return {
            "simulation_id": simulation_id,
            "status": engine.status,
            "scenario_data": engine.scenario_data,
            "config": engine.config,
            "start_time": engine.start_time
        }
    
    async def start_playback(
        self,
        db: AsyncSession,
        simulation_id: str,
        speed: float = 1.0,
        auto_advance: bool = True
    ) -> Dict:
        """자동 재생 시작"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        # 자동 재생 로직 (백그라운드 태스크로 구현 가능)
        # 여기서는 간단히 상태만 업데이트
        engine.session_data["playback_mode"] = True
        engine.session_data["playback_speed"] = speed
        engine.session_data["auto_advance"] = auto_advance
        
        return engine._get_current_state()
    
    async def pause_simulation(self, db: AsyncSession, simulation_id: str) -> None:
        """시뮬레이션 일시정지"""
        engine = self.active_simulations.get(simulation_id)
        if engine:
            engine.session_data["paused"] = True
    
    async def resume_simulation(self, db: AsyncSession, simulation_id: str) -> None:
        """시뮬레이션 재개"""
        engine = self.active_simulations.get(simulation_id)
        if engine:
            engine.session_data["paused"] = False
    
    async def get_debug_info(self, db: AsyncSession, simulation_id: str) -> Dict:
        """디버그 정보 조회"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        return {
            "current_state": engine._get_current_state(),
            "variables": engine.session_data,
            "call_stack": engine.execution_history[-10:],  # 최근 10개
            "performance_metrics": {
                "execution_time": time.time() - engine.start_time,
                "steps_count": len(engine.execution_history),
                "avg_step_time": (time.time() - engine.start_time) / max(len(engine.execution_history), 1)
            },
            "memory_usage": len(str(engine.session_data)),  # 간단한 메모리 사용량
            "execution_trace": engine.execution_history
        }
    
    async def validate_simulation(self, db: AsyncSession, simulation_id: str) -> Dict:
        """시뮬레이션 유효성 검증"""
        engine = self.active_simulations.get(simulation_id)
        if not engine:
            raise NotFoundError("시뮬레이션을 찾을 수 없습니다.")
        
        errors = []
        warnings = []
        recommendations = []
        
        # 시나리오 구조 검증
        nodes = engine.scenario_data.get("nodes", [])
        connections = engine.scenario_data.get("connections", [])
        
        # 시작 노드 확인
        start_nodes = [n for n in nodes if n.get("node_type") == NodeType.START]
        if not start_nodes:
            errors.append("시작 노드가 없습니다.")
        elif len(start_nodes) > 1:
            warnings.append("시작 노드가 여러 개 있습니다.")
        
        # 종료 노드 확인
        end_nodes = [n for n in nodes if n.get("node_type") == NodeType.END]
        if not end_nodes:
            warnings.append("종료 노드가 없습니다.")
        
        # 연결 검증
        node_ids = {n.get("node_id") for n in nodes}
        for conn in connections:
            source = conn.get("source_node_id")
            target = conn.get("target_node_id")
            
            if source not in node_ids:
                errors.append(f"존재하지 않는 소스 노드: {source}")
            if target not in node_ids:
                errors.append(f"존재하지 않는 타겟 노드: {target}")
        
        # 고립된 노드 확인
        connected_nodes = set()
        for conn in connections:
            connected_nodes.add(conn.get("source_node_id"))
            connected_nodes.add(conn.get("target_node_id"))
        
        isolated_nodes = node_ids - connected_nodes
        if isolated_nodes:
            warnings.append(f"고립된 노드들: {', '.join(isolated_nodes)}")
        
        # 권장사항
        if len(nodes) > 20:
            recommendations.append("노드가 많습니다. 시나리오를 간소화하는 것을 고려해보세요.")
        
        # 커버리지 계산 (실행된 노드 비율)
        executed_nodes = {step.get("node_id") for step in engine.execution_history}
        coverage = len(executed_nodes) / len(nodes) * 100 if nodes else 0
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations,
            "coverage": coverage
        }
