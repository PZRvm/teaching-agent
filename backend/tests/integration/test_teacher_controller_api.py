"""TeacherSessionController REST API 集成测试."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app
from models.checkpoint.persistence_service import CheckpointPlanPersistence
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
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
class TestTeacherControllerAPI:
    """TeacherSessionController REST API 测试"""

    async def test_get_checkpoint_plan_returns_plan(self, db_session, override_get_db):
        """测试 GET /checkpoint-plans/{session_id} 返回检查点计划"""
        # Arrange - 创建 teaching session 和检查点计划
        session = TeachingSessionModel(
            topic="Python 变量与数据类型",
            teaching_mode="heuristic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        plan = CheckpointPlan(
            topic="Python 变量与数据类型",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="Python 变量的定义与赋值",
                    key_point="Python 是动态类型语言",
                    checkpoint_question="什么是变量？",
                    state=CheckpointState.PENDING,
                )
            ],
            current_index=0,
        )
        persistence = CheckpointPlanPersistence(db_session)
        session_id = session.id
        await persistence.save_plan(session_id=session_id, plan=plan)

        # Act - 获取检查点计划
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(f"/checkpoint-plans/{session_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Python 变量与数据类型"
        assert len(data["checkpoints"]) == 1
        assert data["checkpoints"][0]["title"] == "Python 变量的定义与赋值"

    async def test_edit_checkpoint_plan_modifies_plan(self, db_session, override_get_db):
        """测试 PUT /checkpoint-plans/{session_id} 修改检查点计划"""
        # Arrange - 创建 teaching session 和初始检查点计划
        session = TeachingSessionModel(
            topic="Python 变量与数据类型",
            teaching_mode="heuristic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        original_plan = CheckpointPlan(
            topic="Python 变量与数据类型",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="原始标题",
                    key_point="原始知识点",
                    checkpoint_question="原始问题",
                    state=CheckpointState.PENDING,
                )
            ],
            current_index=0,
        )
        persistence = CheckpointPlanPersistence(db_session)
        session_id = session.id
        await persistence.save_plan(session_id=session_id, plan=original_plan)

        # Act - 编辑检查点计划
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            updated_data = {
                "topic": "Python 变量与数据类型（修改后）",
                "teaching_mode": "heuristic",
                "checkpoints": [
                    {
                        "title": "修改后的标题",
                        "key_point": "修改后的知识点",
                        "checkpoint_question": "修改后的问题",
                    }
                ],
            }
            response = await client.put(f"/checkpoint-plans/{session_id}", json=updated_data)

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 验证修改已保存
        modified_plan = await persistence.load_plan(session_id=session_id)
        assert modified_plan is not None
        assert modified_plan.topic == "Python 变量与数据类型（修改后）"
        assert modified_plan.checkpoints[0].title == "修改后的标题"

    async def test_edit_checkpoint_plan_fails_when_teaching_started(
        self, db_session, override_get_db
    ):
        """测试编辑检查点计划在教学开始后失败"""
        # Arrange - 创建已开始教学的检查点计划
        session = TeachingSessionModel(
            topic="Python 变量",
            teaching_mode="heuristic",
            students_config={"count": 1},
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        plan = CheckpointPlan(
            topic="Python 变量",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="变量定义",
                    key_point="知识点",
                    checkpoint_question="问题",
                    state=CheckpointState.TEACHING,  # 已经开始教学
                )
            ],
            current_index=0,
        )
        persistence = CheckpointPlanPersistence(db_session)
        session_id = session.id
        await persistence.save_plan(session_id=session_id, plan=plan)

        # Act - 尝试编辑
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.put(
                f"/checkpoint-plans/{session_id}",
                json={
                    "topic": "修改",
                    "teaching_mode": "heuristic",
                    "checkpoints": [
                        {"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"}
                    ],
                },
            )

        # Assert
        assert response.status_code == 400
        assert "只能在教学开始前编辑检查点" in response.json()["detail"]

    async def test_edit_checkpoint_plan_fails_when_plan_not_found(self, override_get_db):
        """测试编辑不存在的检查点计划返回404"""
        # Act - 尝试编辑不存在的计划
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.put(
                "/checkpoint-plans/999999",
                json={
                    "topic": "修改",
                    "teaching_mode": "heuristic",
                    "checkpoints": [
                        {"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"}
                    ],
                },
            )

        # Assert
        assert response.status_code == 404
