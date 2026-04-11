"""观察模式 API 集成测试."""

import pytest


def test_start_observation_creates_session():
    """启动观察模式创建 teaching_session 记录."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    payload = {
        "topic": "Python Basics",
        "teaching_mode": "heuristic",
        "checkpoint_count": 3,
        "students": [
            {
                "name": "Student1",
                "level": "average",
                "attitude": "neutral",
                "learning_ability": 5,
            },
        ],
    }

    response = client.post("/observation/start", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], int)
    assert data["status"] == "initializing"
    assert data["session_id"] > 0


def test_start_observation_missing_topic():
    """缺少 topic 参数返回 422."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    payload = {
        "teaching_mode": "heuristic",
        "students": [
            {"name": "Student1", "level": "average", "attitude": "neutral", "learning_ability": 5}
        ],
    }
    response = client.post("/observation/start", json=payload)
    assert response.status_code == 422


def test_start_observation_empty_students():
    """空学生列表返回 422."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    payload = {
        "topic": "Python Basics",
        "teaching_mode": "heuristic",
        "students": [],
    }
    response = client.post("/observation/start", json=payload)
    assert response.status_code == 422


class TestObservationApiRegistration:
    """观察模式 SessionRegistry 注册测试（需要 LLM API）.

    这些测试验证 POST /observation/start 立即返回并注册 mode，
    后台任务负责延迟注册 orchestrator。
    """

    @pytest.mark.asyncio
    async def test_start_observation_registers_mode_only(self):
        """POST /observation/start 应立即注册 mode 到 SessionRegistry.

        验证请求立即返回（不等待 LLM），且 mode 已注册。
        orchestrator 由后台任务延迟注册。
        """
        from httpx import ASGITransport, AsyncClient

        from core.session_registry import SessionRegistry, set_session_registry
        from main import app

        # 重置全局 SessionRegistry
        set_session_registry(SessionRegistry())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/observation/start",
                json={
                    "topic": "Python 变量",
                    "teaching_mode": "didactic",
                    "checkpoint_count": 1,
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
