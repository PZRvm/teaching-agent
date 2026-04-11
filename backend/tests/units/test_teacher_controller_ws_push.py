"""TeacherSessionController WebSocket 推送测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState


def _make_plan(topic: str = "一次函数", teaching_mode: str = "teacher") -> CheckpointPlan:
    """创建测试用 CheckpointPlan（至少一个检查点以满足 min_length=1 约束）."""
    return CheckpointPlan(
        topic=topic,
        teaching_mode=teaching_mode,
        checkpoints=[
            Checkpoint(
                title="检查点1",
                key_point="一次函数定义",
                checkpoint_question="什么是一次函数？",
                state=CheckpointState.PENDING,
            ),
        ],
    )


class TestTeacherControllerWsPush:
    """TeacherSessionController 通过 ConnectionManager 推送学生回答."""

    @pytest.mark.asyncio
    async def test_handle_ask_to_all_broadcasts_answers(self):
        """handle_ask_to_all 通过 ConnectionManager 广播学生回答."""
        from models.session.services.teacher_service import TeacherSessionController

        mock_student = MagicMock()
        mock_student.profile.name = "张三"
        mock_student.ask_question.return_value = "一次函数是 y=kx+b"

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        plan = _make_plan()
        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
        )

        mock_broadcast = AsyncMock()
        with patch("models.session.services.teacher_service.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            controller.handle_ask_to_all("什么是一次函数？")

            mock_broadcast.assert_called()
            call_kwargs = mock_broadcast.call_args[1]
            assert call_kwargs["session_id"] == 1
            message = call_kwargs["message"]
            assert message["type"] == "student_answer"
            assert message["student_name"] == "张三"

    @pytest.mark.asyncio
    async def test_handle_broadcast_lecture_pushes_message(self):
        """handle_broadcast_lecture 通过 ConnectionManager 推送消息."""
        from models.session.services.teacher_service import TeacherSessionController

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        plan = _make_plan()
        controller = TeacherSessionController(
            student_agents=[],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
        )

        mock_broadcast = AsyncMock()
        with patch("models.session.services.teacher_service.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            controller.handle_broadcast_lecture("今天我们学习一次函数")

            mock_broadcast.assert_called_once()
            call_kwargs = mock_broadcast.call_args[1]
            message = call_kwargs["message"]
            assert message["type"] == "message"
            assert message["sender"] == "teacher"
            assert message["message_type"] == "lecture"

    def test_ws_broadcast_skipped_without_event_loop(self):
        """没有运行中的事件循环时，WebSocket 推送被安全跳过."""
        import asyncio

        from models.session.services.teacher_service import TeacherSessionController

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        plan = _make_plan()
        controller = TeacherSessionController(
            student_agents=[],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
        )

        # 确认当前没有运行中的事件循环（同步测试中不存在）
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()

        # 调用不应抛出异常
        with patch("models.session.services.teacher_service.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            controller.handle_broadcast_lecture("测试内容")

            # broadcast 不应被调用（因为没有事件循环来调度任务）
            mock_manager.broadcast.assert_not_called()
