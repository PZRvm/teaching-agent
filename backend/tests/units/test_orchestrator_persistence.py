"""SessionOrchestrator 检查点状态持久化测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState


class TestOrchestratorCheckpointPersistence:
    """验证 SessionOrchestrator 在每次状态变更后持久化到数据库."""

    @pytest.mark.asyncio
    async def test_persist_called_on_teaching_state(self):
        """检查点进入 TEACHING 状态时调用持久化."""
        from models.session.services.observation_service import SessionOrchestrator

        checkpoint = Checkpoint(
            title="变量",
            key_point="变量的定义和使用",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="didactic",
            checkpoints=[checkpoint],
        )
        mock_mm = MagicMock()
        mock_mm.session_memory.session_id = 1

        orchestrator = SessionOrchestrator(
            teacher_agent=MagicMock(),
            student_agents=[],
            checkpoint_plan=plan,
            memory_manager=mock_mm,
        )

        checkpoint.state = CheckpointState.TEACHING
        plan.current_index = 0

        mock_persistence = AsyncMock()
        with (
            patch("core.database.async_session_maker") as mock_session_maker,
            patch(
                "models.checkpoint.services.persistence_service.CheckpointPlanPersistence",
                return_value=mock_persistence,
            ),
        ):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            await orchestrator._persist_checkpoint_state()

            mock_persistence.update_checkpoint_state.assert_called_once_with(
                1, 0, CheckpointState.TEACHING
            )

    @pytest.mark.asyncio
    async def test_persist_called_on_complete_state(self):
        """检查点进入 COMPLETE 状态时调用持久化."""
        from models.session.services.observation_service import SessionOrchestrator

        checkpoint = Checkpoint(
            title="函数",
            key_point="函数的定义和调用",
            checkpoint_question="如何定义函数？",
        )
        plan = CheckpointPlan(
            topic="Python 进阶",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )
        mock_mm = MagicMock()
        mock_mm.session_memory.session_id = 42

        orchestrator = SessionOrchestrator(
            teacher_agent=MagicMock(),
            student_agents=[],
            checkpoint_plan=plan,
            memory_manager=mock_mm,
        )

        checkpoint.state = CheckpointState.COMPLETE
        plan.current_index = 0

        mock_persistence = AsyncMock()
        with (
            patch("core.database.async_session_maker") as mock_session_maker,
            patch(
                "models.checkpoint.services.persistence_service.CheckpointPlanPersistence",
                return_value=mock_persistence,
            ),
        ):
            mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

            await orchestrator._persist_checkpoint_state()

            mock_persistence.update_checkpoint_state.assert_called_once_with(
                42, 0, CheckpointState.COMPLETE
            )

    @pytest.mark.asyncio
    async def test_persist_failure_does_not_crash(self):
        """持久化失败时只记录日志，不抛出异常."""
        from models.session.services.observation_service import SessionOrchestrator

        checkpoint = Checkpoint(
            title="类",
            key_point="类的定义",
            checkpoint_question="如何定义类？",
        )
        plan = CheckpointPlan(
            topic="Python OOP",
            teaching_mode="didactic",
            checkpoints=[checkpoint],
        )
        mock_mm = MagicMock()
        mock_mm.session_memory.session_id = 1

        orchestrator = SessionOrchestrator(
            teacher_agent=MagicMock(),
            student_agents=[],
            checkpoint_plan=plan,
            memory_manager=mock_mm,
        )

        checkpoint.state = CheckpointState.TEACHING
        plan.current_index = 0

        with patch("core.database.async_session_maker", side_effect=Exception("DB connection failed")):
            # 不应抛出异常
            await orchestrator._persist_checkpoint_state()

    @pytest.mark.asyncio
    async def test_teach_checkpoint_calls_persist_three_times_heuristic(self):
        """启发式模式下 _teach_checkpoint 调用 3 次持久化（TEACHING, QUESTIONS, COMPLETE）."""
        from models.session.services.observation_service import SessionOrchestrator

        checkpoint = Checkpoint(
            title="列表",
            key_point="列表操作",
            checkpoint_question="列表有哪些常用方法？",
        )
        plan = CheckpointPlan(
            topic="Python 数据结构",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )
        mock_mm = MagicMock()
        mock_mm.session_memory.session_id = 1
        mock_mm.teacher_memory = MagicMock()

        mock_teacher = MagicMock()
        mock_teacher.deliver_lecture.return_value = "讲授内容"
        mock_teacher.ask_checkpoint_question.return_value = "问题内容"

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=[],
            checkpoint_plan=plan,
            memory_manager=mock_mm,
        )

        persist_mock = AsyncMock()
        orchestrator._persist_checkpoint_state = persist_mock

        # Mock WebSocket push to avoid needing ConnectionManager
        orchestrator._ws_push_callback = AsyncMock()

        with (
            patch.object(orchestrator, "_deliver_checkpoint_lecture", new_callable=AsyncMock),
            patch.object(orchestrator, "_handle_checkpoint_questions", new_callable=AsyncMock),
            patch.object(orchestrator, "_trigger_observer_learning_for_checkpoint", new_callable=AsyncMock),
        ):
            mock_mm.summarize_checkpoint = MagicMock()
            await orchestrator._teach_checkpoint(checkpoint)

        # 启发式模式: TEACHING + QUESTIONS + COMPLETE = 3 次持久化
        assert persist_mock.call_count == 3

    @pytest.mark.asyncio
    async def test_teach_checkpoint_calls_persist_two_times_didactic(self):
        """灌输式模式下 _teach_checkpoint 调用 2 次持久化（TEACHING, COMPLETE）."""
        from models.session.services.observation_service import SessionOrchestrator

        checkpoint = Checkpoint(
            title="变量",
            key_point="变量定义",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="didactic",
            checkpoints=[checkpoint],
        )
        mock_mm = MagicMock()
        mock_mm.session_memory.session_id = 1
        mock_mm.teacher_memory = MagicMock()

        orchestrator = SessionOrchestrator(
            teacher_agent=MagicMock(),
            student_agents=[],
            checkpoint_plan=plan,
            memory_manager=mock_mm,
        )

        persist_mock = AsyncMock()
        orchestrator._persist_checkpoint_state = persist_mock
        orchestrator._ws_push_callback = AsyncMock()

        with (
            patch.object(orchestrator, "_deliver_checkpoint_lecture", new_callable=AsyncMock),
            patch.object(orchestrator, "_trigger_observer_learning_for_checkpoint", new_callable=AsyncMock),
        ):
            mock_mm.summarize_checkpoint = MagicMock()
            await orchestrator._teach_checkpoint(checkpoint)

        # 灌输式模式: TEACHING + COMPLETE = 2 次持久化
        assert persist_mock.call_count == 2
