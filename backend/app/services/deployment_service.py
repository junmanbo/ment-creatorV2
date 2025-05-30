# app/services/deployment_service.py
"""
배포 관리 서비스
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.deployment import Deployment
from app.models.scenario import Scenario
from app.schemas.deployment import DeploymentCreate, DeploymentUpdate
from app.services.base import BaseService
from app.utils.constants import DeploymentEnvironment, DeploymentStatus
from app.utils.logger import logger


class DeploymentService(BaseService[Deployment, DeploymentCreate, DeploymentUpdate]):
    """배포 서비스 클래스"""
    
    def __init__(self):
        super().__init__(Deployment)
    
    async def deploy_scenario(
        self,
        db: AsyncSession,
        scenario_id: int,
        environment: DeploymentEnvironment,
        version: str,
        deployed_by: int,
        config: Optional[dict] = None
    ) -> Deployment:
        """시나리오 배포"""
        
        # 시나리오 존재 확인
        scenario_query = select(Scenario).where(Scenario.id == scenario_id)
        result = await db.execute(scenario_query)
        scenario = result.scalars().first()
        
        if not scenario:
            raise NotFoundError(f"Scenario with id {scenario_id} not found")
        
        # 기존 활성 배포 확인
        existing_deployment_query = select(Deployment).where(
            Deployment.scenario_id == scenario_id,
            Deployment.environment == environment,
            Deployment.status == DeploymentStatus.DEPLOYED
        )
        result = await db.execute(existing_deployment_query)
        existing_deployment = result.scalars().first()
        
        if existing_deployment:
            logger.info(f"Found existing deployment {existing_deployment.id}, will rollback")
        
        # 새 배포 생성
        deployment_data = DeploymentCreate(
            scenario_id=scenario_id,
            environment=environment,
            version=version,
            config=config or {},
            deployed_by=deployed_by,
            status=DeploymentStatus.PENDING
        )
        
        deployment = await self.create(db, obj_in=deployment_data)
        
        try:
            # 배포 로직 실행 (실제 배포는 별도 서비스에서 처리)
            await self._execute_deployment(db, deployment)
            
            # 배포 성공 시 상태 업데이트
            deployment.status = DeploymentStatus.DEPLOYED
            await db.commit()
            
            # 이전 배포 비활성화
            if existing_deployment:
                existing_deployment.status = DeploymentStatus.ROLLED_BACK
                await db.commit()
            
            logger.info(f"Deployment {deployment.id} completed successfully")
            
        except Exception as e:
            # 배포 실패 시 상태 업데이트
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            await db.commit()
            
            logger.error(f"Deployment {deployment.id} failed: {e}")
            raise ValidationError(f"Deployment failed: {e}")
        
        return deployment
    
    async def rollback_deployment(
        self,
        db: AsyncSession,
        deployment_id: int,
        rollback_version: Optional[str] = None
    ) -> Deployment:
        """배포 롤백"""
        
        deployment = await self.get_or_404(db, deployment_id)
        
        if deployment.status != DeploymentStatus.DEPLOYED:
            raise ValidationError("Can only rollback deployed deployments")
        
        try:
            # 롤백 로직 실행
            await self._execute_rollback(db, deployment, rollback_version)
            
            # 롤백 성공 시 상태 업데이트
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.rollback_version = rollback_version
            await db.commit()
            
            logger.info(f"Deployment {deployment_id} rolled back successfully")
            
        except Exception as e:
            deployment.error_message = str(e)
            await db.commit()
            
            logger.error(f"Rollback failed for deployment {deployment_id}: {e}")
            raise ValidationError(f"Rollback failed: {e}")
        
        return deployment
    
    async def get_deployments_by_scenario(
        self,
        db: AsyncSession,
        scenario_id: int,
        environment: Optional[DeploymentEnvironment] = None
    ) -> List[Deployment]:
        """시나리오별 배포 목록 조회"""
        
        query = select(self.model).where(self.model.scenario_id == scenario_id)
        
        if environment:
            query = query.where(self.model.environment == environment)
        
        query = query.order_by(self.model.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_active_deployment(
        self,
        db: AsyncSession,
        scenario_id: int,
        environment: DeploymentEnvironment
    ) -> Optional[Deployment]:
        """활성 배포 조회"""
        
        query = select(self.model).where(
            self.model.scenario_id == scenario_id,
            self.model.environment == environment,
            self.model.status == DeploymentStatus.DEPLOYED
        )
        
        result = await db.execute(query)
        return result.scalars().first()
    
    async def _execute_deployment(self, db: AsyncSession, deployment: Deployment):
        """실제 배포 실행 (구현 필요)"""
        # TODO: 실제 배포 로직 구현
        # - 시나리오 데이터 검증
        # - 배포 환경에 시나리오 업로드
        # - 헬스체크 수행
        import asyncio
        await asyncio.sleep(1)  # 임시 배포 시뮬레이션
        logger.info(f"Executing deployment {deployment.id}")
    
    async def _execute_rollback(
        self, 
        db: AsyncSession, 
        deployment: Deployment, 
        rollback_version: Optional[str]
    ):
        """실제 롤백 실행 (구현 필요)"""
        # TODO: 실제 롤백 로직 구현
        # - 이전 버전으로 복원
        # - 헬스체크 수행
        import asyncio
        await asyncio.sleep(1)  # 임시 롤백 시뮬레이션
        logger.info(f"Executing rollback for deployment {deployment.id}")
