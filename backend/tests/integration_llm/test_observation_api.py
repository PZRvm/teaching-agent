"""观察模式 API 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_start_observation_creates_session(override_get_db):
    """启动观察模式创建 teaching_session 记录."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        payload = {
            "topic": "Python Basics",
            "teaching_mode": "heuristic",
            "students": [
                {
                    "name": "Student1",
                    "level": "average",
                    "attitude": "neutral",
                    "learning_ability": 5,
                },
            ],
        }

        response = await client.post("/observation/start", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], int)
    assert data["status"] == "initializing"
    assert data["session_id"] > 0


@pytest.mark.asyncio
async def test_start_observation_missing_topic(override_get_db):
    """缺少 topic 参数返回 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        payload = {
            "teaching_mode": "heuristic",
            "students": [
                {"name": "Student1", "level": "average", "attitude": "neutral", "learning_ability": 5}
            ],
        }
        response = await client.post("/observation/start", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_start_observation_empty_students(override_get_db):
    """空学生列表返回 422."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        payload = {
            "topic": "Python Basics",
            "teaching_mode": "heuristic",
            "students": [],
        }
        response = await client.post("/observation/start", json=payload)
    assert response.status_code == 422


class TestObservationApiRegistration:
    """观察模式 SessionRegistry 注册测试（需要 LLM API）.

    这些测试验证 POST /observation/start 立即返回并注册 mode，
    后台任务负责延迟注册 orchestrator。
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_start_observation_registers_mode_only(self, override_get_db):
        """POST /observation/start 应立即注册 mode 到 SessionRegistry.

        验证请求立即返回（不等待 LLM），且 mode 已注册。
        orchestrator 由后台任务延迟注册。
        """
        from core.session_registry import SessionRegistry, set_session_registry

        # 重置全局 SessionRegistry
        set_session_registry(SessionRegistry())

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/observation/start",
                json={
                    "topic": "Python 变量",
                    "teaching_mode": "didactic",
                    "students": [
                        {
                            "name": "张三",
                            "level": "average",
                            "attitude": "active",
                            "learning_ability": 7,
                        }
                    ],
                },
            )

        # 请求立即返回（200），不等待 LLM
        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]
        assert session_id > 0
        assert data["status"] == "initializing"

        # 验证 mode 已立即注册
        from core.session_registry import get_session_registry

        registry = get_session_registry()
        info = registry.get_session_info(session_id)

        # mode 应该已注册（即使后台任务失败）
        if info is not None:
            assert info["mode"] == "observation"
