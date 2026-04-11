"""SessionOrchestrator WebSocket 推送集成测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState


class TestOrchestratorWsPush:
    """Orchestrator 通过 ConnectionManager 推送 WebSocket 消息."""

    @pytest.mark.asyncio
    async def test_ws_push_uses_connection_manager(self):
        """_ws_push_checkpoint_state 通过 ConnectionManager 广播消息."""
        from models.session.services.observation_service import SessionOrchestrator

        mock_teacher = MagicMock()
        mock_students = []
        checkpoint = Checkpoint(
            title="变量",
            key_point="变量的定义和使用",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )
        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=mock_students,
            checkpoint_plan=plan,
            memory_manager=mock_memory_manager,
        )

        # Mock ConnectionManager.broadcast
        mock_broadcast = AsyncMock()
        with patch("models.session.services.observation_service.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            await orchestrator._ws_push_checkpoint_state(checkpoint)

            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args
            assert call_args[0][0] == 1  # session_id
            message = call_args[0][1]
            assert message["type"] == "checkpoint_state_change"
            assert "checkpoint" in message
            assert "progress" in message

    @pytest.mark.asyncio
    async def test_ws_push_skips_when_no_connections(self):
        """_ws_push_checkpoint_state 在无活跃连接时不广播."""
        from models.session.services.observation_service import SessionOrchestrator

        mock_teacher = MagicMock()
        mock_students = []
        checkpoint = Checkpoint(
            title="变量",
            key_point="变量的定义和使用",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )
        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=mock_students,
            checkpoint_plan=plan,
            memory_manager=mock_memory_manager,
        )

        mock_broadcast = AsyncMock()
        with patch("models.session.services.observation_service.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 0
            mock_get_cm.return_value = mock_manager

            await orchestrator._ws_push_checkpoint_state(checkpoint)

            mock_broadcast.assert_not_called()

    @pytest.mark.asyncio
    async def test_ws_push_message_format(self):
        """_ws_push_checkpoint_state 广播的消息格式正确."""
        from models.session.services.observation_service import SessionOrchestrator

        mock_teacher = MagicMock()
        mock_students = []
        checkpoint = Checkpoint(
            title="变量",
            key_point="变量的定义和使用",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )
        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 42

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=mock_students,
            checkpoint_plan=plan,
            memory_manager=mock_memory_manager,
        )

        # Set checkpoint state to TEACHING for the test
        checkpoint.state = CheckpointState.TEACHING

        mock_broadcast = AsyncMock()
        with patch("models.session.services.observation_service.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            await orchestrator._ws_push_checkpoint_state(checkpoint)

            call_args = mock_broadcast.call_args
            assert call_args[0][0] == 42  # session_id
            message = call_args[0][1]

            # Verify top-level structure
            assert message["type"] == "checkpoint_state_change"
            assert message["session_id"] == 42

            # Verify checkpoint sub-dict
            assert message["checkpoint"]["title"] == "变量"
            assert message["checkpoint"]["key_point"] == "变量的定义和使用"
            assert message["checkpoint"]["state"] == "teaching"

            # Verify progress sub-dict
            assert message["progress"]["current"] == 1  # current_index + 1
            assert message["progress"]["total"] == 1
            assert message["progress"]["completed"] == 0
