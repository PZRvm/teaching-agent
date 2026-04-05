"""Checkpoint API 集成测试."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from main import app
from orm.checkpoint_plan import CheckpointPlanModel
from orm.teaching_session import TeachingSessionModel


@pytest_asyncio.fixture
async def override_get_db(db_session):
    """Override get_db dependency for tests."""
    from core.database import get_db

    async def override_get_db_test():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db_test
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestCheckpointAPI:
    """Checkpoint API 集成测试."""

    async def test_create_checkpoint_plan(self, db_session, override_get_db):
        """POST /checkpoint-plans/ - 创建检查点计划."""
        # 先创建 teaching_session
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config={"count": 3},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        # 使用 AsyncClient 覆盖 get_db 依赖
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            plan_data = {
                "topic": "Python 基础",
                "teaching_mode": "heuristic",
                "checkpoints": [
                    {
                        "title": "变量与数据类型",
                        "key_point": "int, float, str",
                        "checkpoint_question": "Python 有哪些基本数据类型?",
                    }
                ],
            }

            response = await client.post(
                f"/checkpoint-plans/?session_id={session.id}", json=plan_data
            )

            assert response.status_code == 200
            data = response.json()
            assert "plan_id" in data
            assert data["plan_id"] > 0

    async def test_get_checkpoint_plan(self, db_session, override_get_db):
        """GET /checkpoint-plans/{session_id} - 获取检查点计划."""
        # 创建 session 和 plan
        session = TeachingSessionModel(
            topic="测试主题",
            teaching_mode="didactic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        plan_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data={
                "topic": "测试主题",
                "teaching_mode": "didactic",
                "checkpoints": [{"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"}],
                "current_index": 0,
            },
        )
        db_session.add(plan_record)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(f"/checkpoint-plans/{session.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["topic"] == "测试主题"
            assert data["teaching_mode"] == "didactic"

    async def test_get_nonexistent_plan_returns_404(self, db_session, override_get_db):
        """GET /checkpoint-plans/{session_id} - 不存在的计划返回 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/checkpoint-plans/99999")

            assert response.status_code == 404

    async def test_update_checkpoint_state(self, db_session, override_get_db):
        """PUT /checkpoint-plans/{session_id}/checkpoints/{index}/state - 更新检查点状态."""
        # 创建 session 和 plan
        session = TeachingSessionModel(
            topic="状态测试",
            teaching_mode="heuristic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        plan_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data={
                "topic": "状态测试",
                "teaching_mode": "heuristic",
                "checkpoints": [
                    {
                        "title": "C1",
                        "key_point": "K1",
                        "checkpoint_question": "Q1",
                        "state": "pending",
                    },
                    {
                        "title": "C2",
                        "key_point": "K2",
                        "checkpoint_question": "Q2",
                        "state": "pending",
                    },
                ],
                "current_index": 0,
            },
        )
        db_session.add(plan_record)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.put(
                f"/checkpoint-plans/{session.id}/checkpoints/0/state",
                json={"new_state": "teaching"},
            )

            assert response.status_code == 200

            # 验证状态已更新
            result = await db_session.execute(
                select(CheckpointPlanModel).where(CheckpointPlanModel.session_id == session.id)
            )
            updated = result.scalar_one()
            assert updated.plan_data["checkpoints"][0]["state"] == "teaching"

    async def test_advance_checkpoint(self, db_session, override_get_db):
        """PUT /checkpoint-plans/{session_id}/advance - 推进到下一个检查点."""
        # 创建 session 和 plan
        session = TeachingSessionModel(
            topic="推进测试",
            teaching_mode="heuristic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        plan_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data={
                "topic": "推进测试",
                "teaching_mode": "heuristic",
                "checkpoints": [
                    {
                        "title": "C1",
                        "key_point": "K1",
                        "checkpoint_question": "Q1",
                        "state": "complete",
                    },
                    {
                        "title": "C2",
                        "key_point": "K2",
                        "checkpoint_question": "Q2",
                        "state": "pending",
                    },
                ],
                "current_index": 0,
            },
        )
        db_session.add(plan_record)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.put(f"/checkpoint-plans/{session.id}/advance")

            assert response.status_code == 200
            data = response.json()
            assert data["current_index"] == 1

    async def test_delete_checkpoint_plan(self, db_session, override_get_db):
        """DELETE /checkpoint-plans/{session_id} - 删除检查点计划."""
        # 创建 session 和 plan
        session = TeachingSessionModel(
            topic="删除测试",
            teaching_mode="didactic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        plan_record = CheckpointPlanModel(
            session_id=session.id,
            plan_data={
                "topic": "删除测试",
                "teaching_mode": "didactic",
                "checkpoints": [{"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"}],
                "current_index": 0,
            },
        )
        db_session.add(plan_record)
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.delete(f"/checkpoint-plans/{session.id}")

            assert response.status_code == 200

            # 验证已删除
            result = await db_session.execute(
                select(CheckpointPlanModel).where(CheckpointPlanModel.session_id == session.id)
            )
            assert result.scalar_one_or_none() is None
