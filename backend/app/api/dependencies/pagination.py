"""
페이징 의존성
"""
from typing import Optional

from fastapi import Query

from app.core.config import settings


class PaginationParams:
    """페이징 파라미터"""
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="페이지 번호"),
        size: int = Query(
            settings.DEFAULT_PAGE_SIZE, 
            ge=1, 
            le=settings.MAX_PAGE_SIZE, 
            description="페이지 크기"
        )
    ):
        self.page = page
        self.size = size
        self.skip = (page - 1) * size
        self.limit = size


class SearchParams:
    """검색 파라미터"""
    
    def __init__(
        self,
        search: Optional[str] = Query(None, min_length=2, description="검색어"),
        category: Optional[str] = Query(None, description="카테고리 필터"),
        status: Optional[str] = Query(None, description="상태 필터"),
        created_by: Optional[int] = Query(None, description="작성자 필터")
    ):
        self.search = search
        self.category = category
        self.status = status
        self.created_by = created_by
