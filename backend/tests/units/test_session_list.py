"""会话列表 API 单元测试."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from orm.checkpoint_plan import CheckpointPlanModel
from orm.teaching_session import TeachingSessionModel


@pytest.mark.asyncio
class TestSessionListAPI:
    """GET /sessions/ 接口测试."""

    async def test_empty_list_returns_empty_array(self, override_get_db):
        """没有会话时返回空数组."""
        from httpx import ASGITransport, AsyncClient

        from main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get("/sessions/")

        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_sessions_with_checkpoint_progress(self, db_session, test_engine):
        """有会话和检查点计划时，返回完整数据."""
        session = TeachingSessionModel(
            topic="Python 变量",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}, {"name": "李四"}],
            status="completed",
            start_time=datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            end_time=datetime(2026, 4, 12, 15, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            duration_seconds=3600,
        )
        db_session.add(session)
        await db_session.flush()

        plan = CheckpointPlanModel(
            session_id=session.id,
            plan_data={
                "topic": "Python 变量",
                "teaching_mode": "heuristic",
                "current_index": 2,
                "checkpoints": [
                    {"title": "变量介绍", "state": "complete"},
                    {"title": "数据类型", "state": "complete"},
                    {"title": "运算符", "state": "teaching"},
                    {"title": "控制流", "state": "pending"},
                ],
            },
        )
        db_session.add(plan)
        await db_session.commit()

        from httpx import ASGITransport, AsyncClient

        from core.database import get_db
        from main import app

        app.dependency_overrides[get_db] = lambda: db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/sessions/")

            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1

            item = data[0]
            assert item["id"] == session.id
            assert item["topic"] == "Python 变量"
            assert item["teaching_mode"] == "heuristic"
            assert item["student_count"] == 2
            assert item["checkpoint_progress"]["total"] == 4
            assert item["checkpoint_progress"]["completed"] == 2
            assert item["checkpoint_progress"]["current_index"] == 2
        finally:
            app.dependency_overrides.clear()

    async def test_session_without_checkpoint_plan_returns_null_progress(
        self, db_session, test_engine
    ):
        """没有检查点计划的会话返回 checkpoint_progress 为 null."""
        session = TeachingSessionModel(
            topic="函数基础",
            teaching_mode="didactic",
            students_config=[{"name": "王五"}],
            status="interrupted",
            start_time=datetime(2026, 4, 13, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        db_session.add(session)
        await db_session.commit()

        from httpx import ASGITransport, AsyncClient

        from core.database import get_db
        from main import app

        app.dependency_overrides[get_db] = lambda: db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/sessions/")

            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["checkpoint_progress"] is None
        finally:
            app.dependency_overrides.clear()

    async def test_sessions_ordered_by_start_time_desc(self, db_session, test_engine):
        """会话按 start_time 倒序排列."""
        for topic, hour in [("早期课", 8), ("晚期课", 16)]:
            session = TeachingSessionModel(
                topic=topic,
                teaching_mode="didactic",
                students_config=[],
                status="completed",
                start_time=datetime(2026, 4, 12, hour, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            )
            db_session.add(session)
        await db_session.commit()

        from httpx import ASGITransport, AsyncClient

        from core.database import get_db
        from main import app

        app.dependency_overrides[get_db] = lambda: db_session
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/sessions/")

            data = resp.json()
            assert len(data) == 2
            assert data[0]["topic"] == "晚期课"
            assert data[1]["topic"] == "早期课"
        finally:
            app.dependency_overrides.clear()
