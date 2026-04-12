"""TeacherSessionController 消息推送测试."""

from unittest.mock import MagicMock

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from models.session.schemas import MessageType


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
    """TeacherSessionController 通过 MessageService 推送消息."""

    def test_handle_ask_to_all_calls_emit_message_sync(self):
        """handle_ask_to_all 通过 MessageService 推送问题和学生回答."""
        from models.session.services.teacher_service import TeacherSessionController

        mock_student = MagicMock()
        mock_student.profile.name = "张三"
        mock_student.ask_question.return_value = "一次函数是 y=kx+b"

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        mock_message_service = MagicMock()

        plan = _make_plan()
        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
            message_service=mock_message_service,
        )

        controller.handle_ask_to_all("什么是一次函数？")

        # 应调用 emit_message_sync 两次：一次问题，一次回答
        assert mock_message_service.emit_message_sync.call_count == 2

        # 验证问题消息
        question_call = mock_message_service.emit_message_sync.call_args_list[0]
        q_msg = question_call[0][0]
        assert q_msg.sender == "teacher"
        assert q_msg.message_type == MessageType.CHECKPOINT_QUESTION
        assert q_msg.content == "什么是一次函数？"

        # 验证学生回答消息
        answer_call = mock_message_service.emit_message_sync.call_args_list[1]
        a_msg = answer_call[0][0]
        assert a_msg.sender == "张三"
        assert a_msg.message_type == MessageType.ANSWER_TO_CHECKPOINT
        assert a_msg.content == "一次函数是 y=kx+b"

    def test_handle_broadcast_lecture_calls_emit_message_sync(self):
        """handle_broadcast_lecture 通过 MessageService 推送讲授消息."""
        from models.session.services.teacher_service import TeacherSessionController

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        mock_message_service = MagicMock()

        plan = _make_plan()
        controller = TeacherSessionController(
            student_agents=[],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
            message_service=mock_message_service,
        )

        controller.handle_broadcast_lecture("今天我们学习一次函数")

        mock_message_service.emit_message_sync.assert_called_once()
        msg = mock_message_service.emit_message_sync.call_args[0][0]
        assert msg.sender == "teacher"
        assert msg.message_type == MessageType.LECTURE
        assert msg.content == "今天我们学习一次函数"
        assert msg.receiver == "all"

    def test_handle_teacher_reply_calls_emit_message_sync(self):
        """handle_teacher_reply 通过 MessageService 持久化回复消息."""
        from models.session.services.teacher_service import TeacherSessionController

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        mock_message_service = MagicMock()

        plan = _make_plan()
        controller = TeacherSessionController(
            student_agents=[],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
            message_service=mock_message_service,
        )

        controller.handle_teacher_reply("回答得很好", "张三")

        mock_message_service.emit_message_sync.assert_called_once()
        msg = mock_message_service.emit_message_sync.call_args[0][0]
        assert msg.sender == "teacher"
        assert msg.message_type == MessageType.TEACHER_REPLY
        assert msg.content == "回答得很好"
        assert msg.receiver == "张三"
