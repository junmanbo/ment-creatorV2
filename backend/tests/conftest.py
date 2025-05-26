# tests/conftest.py
"""
pytest 설정 및 공통 픽스처
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_async_session
from app.main import app


# 테스트용 데이터베이스 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """테스트용 데이터베이스 엔진"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # 테이블 정리
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_session(test_engine):
    """테스트용 데이터베이스 세션"""
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(test_session):
    """테스트용 HTTP 클라이언트"""
    
    def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "role": "operator",
        "department": "Test Department",
    }


@pytest.fixture
def sample_scenario_data():
    """샘플 시나리오 데이터"""
    return {
        "name": "테스트 시나리오",
        "description": "테스트용 시나리오입니다.",
        "category": "테스트",
        "version": "1.0",
    }


@pytest.fixture
def sample_voice_actor_data():
    """샘플 성우 데이터"""
    return {
        "name": "김테스트",
        "gender": "female",
        "age_range": "30s",
        "language": "ko",
        "description": "테스트용 성우",
        "characteristics": {
            "tone": "친근함",
            "style": "밝음"
        }
    }
