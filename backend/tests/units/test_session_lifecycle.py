"""会话生命周期管理单元测试."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from orm.teaching_session import TeachingSessionModel


@pytest.mark.asyncio
class TestSessionLifecycle:
    """会话生命周期更新测试."""

    async def test_finalize_session_sets_completed_status(self, db_session, test_engine):
        """finalize_session 应设置 status 为 completed."""
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}],
            status="running",
            start_time=datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        db_session.add(session)
        await db_session.flush()

        from models.observation.service import finalize_session

        await finalize_session(
            db=db_session,
            session_id=session.id,
            status="completed",
        )
        await db_session.commit()

        await db_session.refresh(session)
        assert session.status == "completed"
        assert session.end_time is not None
        assert session.duration_seconds is not None

    async def test_finalize_session_sets_interrupted_status(self, db_session, test_engine):
        """finalize_session 应设置 status 为 interrupted."""
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}],
            status="running",
            start_time=datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        db_session.add(session)
        await db_session.flush()

        from models.observation.service import finalize_session

        await finalize_session(
            db=db_session,
            session_id=session.id,
            status="interrupted",
        )
        await db_session.commit()

        await db_session.refresh(session)
        assert session.status == "interrupted"

    async def test_finalize_session_calculates_duration(self, db_session, test_engine):
        """finalize_session 应正确计算 duration_seconds."""
        start = datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}],
            status="running",
            start_time=start,
        )
        db_session.add(session)
        await db_session.flush()

        from unittest.mock import patch

        fake_end = datetime(2026, 4, 12, 15, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

        with patch("models.observation.service.datetime") as mock_dt:
            mock_dt.now.return_value = fake_end
            from models.observation.service import finalize_session

            await finalize_session(
                db=db_session,
                session_id=session.id,
                status="completed",
            )

        await db_session.commit()

        await db_session.refresh(session)
        assert session.duration_seconds == 5400

    async def test_finalize_session_nonexistent_id_raises(self, db_session, test_engine):
        """finalize_session 对不存在的 session_id 应抛出 ValueError."""
        from models.observation.service import finalize_session

        with pytest.raises(ValueError, match="会话不存在"):
            await finalize_session(
                db=db_session,
                session_id=99999,
                status="completed",
            )
