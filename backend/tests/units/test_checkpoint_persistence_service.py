"""CheckpointPlanPersistence 单元测试."""

import pytest
from sqlalchemy import select

from models.checkpoint.schemas import CheckpointPlan
from orm.checkpoint_plan import CheckpointPlanModel


@pytest.mark.asyncio
class TestCheckpointPlanPersistence:
    """CheckpointPlanPersistence 单元测试."""

    async def test_save_plan_creates_new_record(self, db_session):
        """保存新计划到数据库."""
        from models.checkpoint.persistence_service import CheckpointPlanPersistence

        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="heuristic",
            checkpoints=[
                {
                    "title": "变量与数据类型",
                    "key_point": "int, float, str",
                    "checkpoint_question": "Python 有哪些基本数据类型?",
                }
            ],
        )

        service = CheckpointPlanPersistence(db_session)
        plan_id = await service.save_plan(session_id=1, plan=plan)

        assert plan_id > 0

        result = await db_session.execute(
            select(CheckpointPlanModel).where(CheckpointPlanModel.id == plan_id)
        )
        saved = result.scalar_one()

        assert saved.session_id == 1
        assert saved.plan_data["topic"] == "Python 基础"
        assert saved.plan_data["teaching_mode"] == "heuristic"

    async def test_load_plan_by_session_id(self, db_session):
        """根据 session_id 加载计划."""
        from models.checkpoint.persistence_service import CheckpointPlanPersistence

        # 先保存一个计划
        plan = CheckpointPlan(
            topic="测试主题",
            teaching_mode="didactic",
            checkpoints=[{"title": "T1", "key_point": "K1", "checkpoint_question": "Q1"}],
        )

        service = CheckpointPlanPersistence(db_session)
        plan_id = await service.save_plan(session_id=42, plan=plan)

        # 加载计划
        loaded_plan = await service.load_plan(session_id=42)

        assert loaded_plan is not None
        assert loaded_plan.topic == "测试主题"
        assert loaded_plan.teaching_mode == "didactic"
        assert len(loaded_plan.checkpoints) == 1

    async def test_load_plan_returns_none_for_nonexistent_session(self, db_session):
        """不存在的 session_id 返回 None."""
        from models.checkpoint.persistence_service import CheckpointPlanPersistence

        service = CheckpointPlanPersistence(db_session)
        loaded_plan = await service.load_plan(session_id=99999)

        assert loaded_plan is None

    async def test_update_checkpoint_state(self, db_session):
        """更新检查点状态."""
        from models.checkpoint.schemas import CheckpointState
        from models.checkpoint.persistence_service import CheckpointPlanPersistence

        plan = CheckpointPlan(
            topic="状态测试",
            teaching_mode="heuristic",
            checkpoints=[
                {"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"},
                {"title": "C2", "key_point": "K2", "checkpoint_question": "Q2"},
            ],
        )

        service = CheckpointPlanPersistence(db_session)
        plan_id = await service.save_plan(session_id=1, plan=plan)

        # 更新第一个检查点状态为 complete
        await service.update_checkpoint_state(
            session_id=1, checkpoint_index=0, new_state=CheckpointState.COMPLETE
        )

        # 加载并验证
        loaded_plan = await service.load_plan(session_id=1)
        assert loaded_plan.checkpoints[0].state == CheckpointState.COMPLETE
        assert loaded_plan.checkpoints[1].state == CheckpointState.PENDING

    async def test_advance_to_next_checkpoint(self, db_session):
        """推进到下一个检查点."""
        from models.checkpoint.schemas import CheckpointState
        from models.checkpoint.persistence_service import CheckpointPlanPersistence

        plan = CheckpointPlan(
            topic="推进测试",
            teaching_mode="heuristic",
            checkpoints=[
                {"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"},
                {"title": "C2", "key_point": "K2", "checkpoint_question": "Q2"},
                {"title": "C3", "key_point": "K3", "checkpoint_question": "Q3"},
            ],
        )

        service = CheckpointPlanPersistence(db_session)
        plan_id = await service.save_plan(session_id=1, plan=plan)

        # 推进到下一个
        await service.advance_checkpoint(session_id=1)

        loaded_plan = await service.load_plan(session_id=1)
        assert loaded_plan.current_index == 1
        assert loaded_plan.checkpoints[1].state == CheckpointState.TEACHING

    async def test_delete_plan_by_session_id(self, db_session):
        """删除计划."""
        from models.checkpoint.persistence_service import CheckpointPlanPersistence

        plan = CheckpointPlan(
            topic="删除测试",
            teaching_mode="didactic",
            checkpoints=[{"title": "C1", "key_point": "K1", "checkpoint_question": "Q1"}],
        )

        service = CheckpointPlanPersistence(db_session)
        await service.save_plan(session_id=1, plan=plan)

        # 删除
        await service.delete_plan(session_id=1)

        # 验证已删除
        loaded_plan = await service.load_plan(session_id=1)
        assert loaded_plan is None
