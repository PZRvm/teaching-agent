"""TeacherSessionController 单元测试."""

import pytest
from unittest.mock import Mock

from datetime import datetime
from unittest.mock import Mock

from models.session.teacher_controller import TeacherSessionController
from models.session.schemas import Message, MessageType
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from agents.memories import SessionMemory, TeacherAgentMemory
from agents.student_agent import StudentAgent
from schemas.student import StudentLevel, StudentAttitude, StudentProfile


class TestTeacherSessionControllerInit:
    """TeacherSessionController 初始化测试"""

    def test_init_creates_controller_with_required_components(self):
        """测试初始化创建控制器及其必需组件"""
        # Arrange
        mock_student_agents = [Mock(), Mock()]
        mock_memory_manager = Mock()
        mock_checkpoint_plan = Mock()
        mock_ws_callback = Mock()

        # Act
        controller = TeacherSessionController(
            student_agents=mock_student_agents,
            memory_manager=mock_memory_manager,
            checkpoint_plan=mock_checkpoint_plan,
            ws_push_callback=mock_ws_callback
        )

        # Assert
        assert controller.student_agents == mock_student_agents
        assert controller.memory_manager == mock_memory_manager
        assert controller.checkpoint_plan == mock_checkpoint_plan
        assert controller._ws_push_callback == mock_ws_callback
        assert controller._active_dialogue is None  # 初始无活跃对话
        assert controller._dialogue_round_count == 0


class TestHandleBroadcastLecture:
    """handle_broadcast_lecture 方法测试"""

    def test_handle_broadcast_lecture_records_to_memory(self):
        """测试广播讲授内容记录到记忆系统"""
        # Arrange
        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[Mock()],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )
        lecture_content = "今天我们学习 Python 变量的基本概念"

        # Act
        controller.handle_broadcast_lecture(lecture_content)

        # Assert - 消息被记录到 session_memory
        messages = mock_memory_manager.session_memory.message_history
        assert len(messages) == 1
        assert messages[0].sender == "teacher"
        assert messages[0].content == lecture_content
        assert messages[0].message_type.value == "lecture"
        assert messages[0].receiver == "all"
        assert messages[0].timestamp is not None


class TestHandleAskToAll:
    """handle_ask_to_all 方法测试"""

    def test_handle_ask_to_all_collects_responses_from_all_students(self):
        """测试向全体提问收集所有学生回答"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.should_respond = Mock(return_value=True)
        mock_student1.ask_question = Mock(return_value="Python 是动态类型语言")

        mock_student2 = Mock()
        mock_student2.name = "李四"
        mock_student2.should_respond = Mock(return_value=True)
        mock_student2.ask_question = Mock(return_value="变量不需要声明类型")

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )
        question = "Python 中的变量和数学中的变量有什么区别？"

        # Act
        controller.handle_ask_to_all(question)

        # Assert - 问题消息记录
        messages = mock_memory_manager.session_memory.message_history
        assert len(messages) >= 1
        assert messages[0].sender == "teacher"
        assert messages[0].content == question
        assert messages[0].message_type.value == "checkpoint_question"

        # Assert - 所有学生都被提问
        mock_student1.ask_question.assert_called_once_with(question)
        mock_student2.ask_question.assert_called_once_with(question)

        # Assert - 学生回答被记录（应该包含 answer_to_checkpoint 消息）
        answer_messages = [m for m in messages if m.message_type.value == "answer_to_checkpoint"]
        assert len(answer_messages) == 2
        assert answer_messages[0].sender in ["张三", "李四"]
        assert answer_messages[1].sender in ["张三", "李四"]


class TestHandleAskToStudent:
    """handle_ask_to_student 方法测试"""

    def test_handle_ask_to_student_collects_response_from_target_student(self):
        """测试向单个学生提问收集该学生的回答"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.ask_question = Mock(return_value="Python 是动态类型语言")

        mock_student2 = Mock()
        mock_student2.name = "李四"

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )
        question = "请张三回答：Python 中列表和元组的区别是什么？"

        # Act
        controller.handle_ask_to_student(question, "张三")

        # Assert - 问题消息记录（发送给特定学生）
        messages = mock_memory_manager.session_memory.message_history
        assert len(messages) >= 1
        assert messages[0].sender == "teacher"
        assert messages[0].content == question
        assert messages[0].receiver == "张三"
        assert messages[0].message_type.value == "checkpoint_question"

        # Assert - 只有目标学生被提问
        mock_student1.ask_question.assert_called_once_with(question)
        mock_student2.ask_question.assert_not_called()

        # Assert - 学生回答被记录
        answer_messages = [m for m in messages if m.message_type.value == "answer_to_checkpoint"]
        assert len(answer_messages) == 1
        assert answer_messages[0].sender == "张三"


