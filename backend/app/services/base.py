"""
기본 서비스 클래스
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """기본 서비스 클래스"""
    
    def __init__(self, model: Type[ModelType]):
        """
        Args:
            model: SQLAlchemy 모델 클래스
        """
        self.model = model
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """ID로 객체 조회"""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()
    
    async def get_or_404(self, db: AsyncSession, id: Any) -> ModelType:
        """ID로 객체 조회 (없으면 404 에러)"""
        obj = await self.get(db, id)
        if not obj:
            raise NotFoundError(f"{self.model.__name__} not found with id: {id}")
        return obj
    
    async def get_multi(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """여러 객체 조회"""
        query = select(self.model)
        
        # 필터 적용
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def count(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """객체 개수 조회"""
        query = select(func.count(self.model.id))
        
        # 필터 적용
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar()
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: Union[BaseModel, Dict[str, Any]]
    ) -> ModelType:
        """객체 생성"""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump()
            
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[BaseModel, Dict[str, Any]]
    ) -> ModelType:
        """객체 수정"""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, *, id: int) -> ModelType:
        """객체 삭제"""
        obj = await self.get_or_404(db, id)
        await db.delete(obj)
        await db.commit()
        return obj
