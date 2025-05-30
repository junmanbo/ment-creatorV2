"""
데이터베이스 의존성
"""
from typing import Generator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal


async def get_async_session() -> Generator[AsyncSession, None, None]:
    """비동기 세션 생성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
