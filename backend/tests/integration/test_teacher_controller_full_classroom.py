"""TeacherSessionController 全课堂流程集成测试."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from models.session.teacher_controller import TeacherSessionController
from models.session.schemas import Message, MessageType
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from agents.memories import SessionMemory


@pytest.mark.asyncio
class TestTeacherControllerFullClassroomFlow:
    """TeacherSessionController 全课堂流程集成测试"""

    async def test_full_classroom_teaching_flow(self, db_session):
        """测试完整课堂教学流程：讲授 → 提问 → 对话 → 作业"""
        # Arrange - 创建两个 Mock 学生（模拟真实学生行为）
        mock_student1 = Mock()
        mock_student1.profile.name = "张三"
        mock_student1.ask_question = Mock(return_value="Python 是动态类型语言，变量不需要声明类型")
        mock_student1.update_knowledge = Mock()

        mock_student2 = Mock()
        mock_student2.profile.name = "李四"
        mock_student2.ask_question = Mock(return_value="变量不需要声明类型，可以直接赋值")
        mock_student2.update_knowledge = Mock()

        # 创建简化的记忆管理器（使用 Mock）
        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = SessionMemory(session_id=1, topic="Python")
        mock_memory_manager.session_memory.message_history = []

        # 创建检查点计划
        checkpoint_plan = CheckpointPlan(
            topic="Python 变量与数据类型",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="Python 变量的定义与赋值",
                    key_point="Python 是动态类型语言，变量无需声明类型",
                    checkpoint_question="Python 中的变量和数学中的变量有什么区别？",
                    state=CheckpointState.TEACHING,
                ),
                Checkpoint(
                    title="Python 数据类型：列表和元组",
                    key_point="列表是可变的，元组是不可变的",
                    checkpoint_question="列表和元组的区别是什么？",
                    state=CheckpointState.PENDING,
                ),
            ],
        )

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=checkpoint_plan,
            ws_push_callback=None,
        )

        # Act 1: 教师讲授
        controller.handle_broadcast_lecture("今天我们学习 Python 变量的基本概念")
        assert len(mock_memory_manager.session_memory.message_history) == 1
        assert mock_memory_manager.session_memory.message_history[0].message_type == MessageType.LECTURE

        # Act 2: 教师向全体提问
        controller.handle_ask_to_all("Python 中有哪些基本数据类型？")
        messages = mock_memory_manager.session_memory.message_history
        question_msg = [m for m in messages if m.message_type == MessageType.CHECKPOINT_QUESTION]
        assert len(question_msg) == 1

        # Act 3: 教师向单个学生提问
        controller.handle_ask_to_student("请张三回答：如何定义一个列表？", "张三")
        answer_msgs = [m for m in mock_memory_manager.session_memory.message_history if m.message_type == MessageType.ANSWER_TO_CHECKPOINT]
        assert len(answer_msgs) >= 1
        assert any(m.sender == "张三" for m in answer_msgs)

        # Act 4: 教师回复学生
        controller.handle_teacher_reply("张三的回答很正确！列表用方括号定义。", "张三")
        reply_msgs = [m for m in mock_memory_manager.session_memory.message_history if m.message_type == MessageType.TEACHER_REPLY]
        assert len(reply_msgs) == 1
        assert reply_msgs[0].receiver == "张三"

        # Assert - 对话状态被跟踪
        assert controller._active_dialogue is not None
        assert controller._active_dialogue["student_name"] == "张三"
        assert controller._dialogue_round_count == 1

        # Act 5: 结束对话
        controller.handle_end_dialogue()
        assert controller._active_dialogue is None
        assert controller._dialogue_round_count == 0

        # Act 6: 推进到下一个检查点
        controller.handle_advance_checkpoint()

        # Act 7: 布置作业
        controller.handle_assign_homework("完成列表和元组的练习题")
        hw_msg = [m for m in mock_memory_manager.session_memory.message_history if m.message_type == MessageType.ASSIGN_HOMEWORK]
        assert len(hw_msg) == 1

        # Final Assert - 检查消息历史完整性
        assert len(mock_memory_manager.session_memory.message_history) >= 6  # 至少包含6条消息
        message_types = [m.message_type for m in mock_memory_manager.session_memory.message_history]
        assert MessageType.LECTURE in message_types
        assert MessageType.CHECKPOINT_QUESTION in message_types
        assert MessageType.ANSWER_TO_CHECKPOINT in message_types
        assert MessageType.TEACHER_REPLY in message_types
        assert MessageType.ASSIGN_HOMEWORK in message_types

    async def test_multi_round_dialogue_flow(self, db_session):
        """测试多轮对话流程"""
        # Arrange - 创建 Mock 学生
        mock_student = Mock()
        mock_student.name = "张三"
        mock_student.ask_question = Mock(return_value="这是学生的回答")

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = SessionMemory(session_id=1, topic="Python")
        mock_memory_manager.session_memory.message_history = []

        checkpoint_plan = CheckpointPlan(
            topic="Python 函数基础",
            teaching_mode="discussion",
            checkpoints=[
                Checkpoint(
                    title="函数定义",
                    key_point="函数用 def 关键字定义",
                    checkpoint_question="如何定义一个函数？",
                    state=CheckpointState.TEACHING,
                ),
            ],
        )

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=checkpoint_plan,
            ws_push_callback=None,
        )

        # Act - 多轮对话
        controller.handle_ask_to_student("第一轮问题", "张三")
        controller.handle_teacher_reply("第一轮回复", "张三")

        controller.handle_teacher_reply("第二轮回复", "张三")
        controller.handle_teacher_reply("第三轮回复", "张三")

        # Assert - 对话轮数正确跟踪
        assert controller._dialogue_round_count == 3
        assert controller._active_dialogue["round_count"] == 3

        # Act - 结束对话
        controller.handle_end_dialogue()

        # Assert - 状态被重置
        assert controller._dialogue_round_count == 0
        assert controller._active_dialogue is None

        # Assert - 消息历史包含3轮对话
        reply_msgs = [m for m in mock_memory_manager.session_memory.message_history if m.message_type == MessageType.TEACHER_REPLY]
        assert len(reply_msgs) == 3

    async def test_error_path_student_not_found(self, db_session):
        """测试错误路径：向不存在的学生提问"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = SessionMemory(session_id=1, topic="Python")
        mock_memory_manager.session_memory.message_history = []

        checkpoint_plan = CheckpointPlan(
            topic="测试主题",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(
                    title="测试检查点",
                    key_point="测试要点",
                    checkpoint_question="测试问题",
                    state=CheckpointState.TEACHING,
                ),
            ],
        )

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=checkpoint_plan,
            ws_push_callback=None,
        )

        # Act - 向不存在的学生提问
        controller.handle_ask_to_student("问题内容", "不存在的王五")

        # Assert - 不会崩溃，问题消息被记录但没有回答
        messages = mock_memory_manager.session_memory.message_history
        question_msgs = [m for m in messages if m.message_type == MessageType.CHECKPOINT_QUESTION]
        assert len(question_msgs) == 1
        answer_msgs = [m for m in messages if m.message_type == MessageType.ANSWER_TO_CHECKPOINT]
        assert len(answer_msgs) == 0  # 没有回答消息
