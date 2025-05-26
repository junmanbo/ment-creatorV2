# tests/test_main.py
"""
메인 애플리케이션 테스트
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """헬스체크 엔드포인트 테스트"""
    response = await client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """루트 엔드포인트 테스트"""
    response = await client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
