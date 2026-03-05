"""API测试"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root():
    """测试根路径"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI小花"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_chat_history_not_found():
    """测试获取不存在的对话历史"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/chat/history/nonexistent_id")

    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == "nonexistent_id"
    assert data["messages"] == []
