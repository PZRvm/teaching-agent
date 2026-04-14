"""会话管理 API 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_get_messages_empty_session(override_get_db):
    """查询不存在 session 的消息返回空列表."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/sessions/999/messages")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_session_status_not_found(override_get_db):
    """查询不存在的 session 返回 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/sessions/999/status")
    assert response.status_code == 404
    assert "detail" in response.json()
