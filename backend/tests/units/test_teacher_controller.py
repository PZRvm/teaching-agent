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

    def test_handle_ask_to_student_with_nonexistent_student_does_not_crash(self):
        """测试向不存在的学生提问不会崩溃"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )
        question = "请王五回答：这个问题"
        nonexistent_student = "王五"

        # Act - should not raise exception
        controller.handle_ask_to_student(question, nonexistent_student)

        # Assert - 问题消息被记录，但没有回答（因为学生不存在）
        messages = mock_memory_manager.session_memory.message_history
        assert len(messages) == 1  # 只有问题消息，没有回答消息
        assert messages[0].message_type.value == "checkpoint_question"
        assert messages[0].receiver == "王五"


class TestHandleTeacherReply:
    """handle_teacher_reply 方法测试"""

    def test_handle_teacher_reply_records_reply_to_memory(self):
        """测试教师回复记录到记忆系统"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )
        reply_content = "张三的回答很好，列表是可变的，元组是不可变的"

        # Act
        controller.handle_teacher_reply(reply_content, "张三")

        # Assert - 回复消息被记录
        messages = mock_memory_manager.session_memory.message_history
        assert len(messages) == 1
        assert messages[0].sender == "teacher"
        assert messages[0].content == reply_content
        assert messages[0].message_type.value == "teacher_reply"
        assert messages[0].receiver == "张三"
        assert messages[0].timestamp is not None

    def test_handle_teacher_reply_tracks_dialogue_round_count(self):
        """测试教师回复增加对话轮数"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act - 多轮对话
        controller.handle_teacher_reply("第一轮回复", "张三")
        controller.handle_teacher_reply("第二轮回复", "张三")
        controller.handle_teacher_reply("第三轮回复", "张三")

        # Assert - 对话轮数递增
        assert controller._dialogue_round_count == 3

    def test_handle_teacher_reply_sets_active_dialogue_state(self):
        """测试教师回复设置活跃对话状态"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act
        controller.handle_teacher_reply("回复内容", "张三")

        # Assert - 活跃对话状态被设置
        assert controller._active_dialogue is not None
        assert controller._active_dialogue["student_name"] == "张三"
        assert controller._active_dialogue["round_count"] == 1


class TestHandleEndDialogue:
    """handle_end_dialogue 方法测试"""

    def test_handle_end_dialogue_clears_active_dialogue_state(self):
        """测试结束对话清除活跃对话状态"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"

        mock_student2 = Mock()
        mock_student2.name = "李四"
        mock_student2.update_knowledge = Mock()  # 旁听学习

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # 先建立对话状态
        controller.handle_teacher_reply("第一轮回复", "张三")
        assert controller._active_dialogue is not None

        # Act
        controller.handle_end_dialogue()

        # Assert - 对话状态被清除
        assert controller._active_dialogue is None
        assert controller._dialogue_round_count == 0

    def test_handle_end_dialogue_triggers_observer_learning(self):
        """测试结束对话触发旁听学习"""
        # Arrange
        from schemas.student import StudentLevel, StudentAttitude, StudentProfile

        # 创建两个学生：张三参与对话，李四旁听
        profile1 = StudentProfile(
            name="张三",
            level=StudentLevel.AVERAGE,
            attitude=StudentAttitude.ACTIVE,
            learning_ability=8
        )
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.profile = profile1

        profile2 = StudentProfile(
            name="李四",
            level=StudentLevel.AVERAGE,
            attitude=StudentAttitude.NEUTRAL,
            learning_ability=6
        )
        mock_student2 = Mock()
        mock_student2.name = "李四"
        mock_student2.profile = profile2
        mock_student2.update_knowledge = Mock()

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act - 张三和教师对话后结束
        controller.handle_teacher_reply("回复张三", "张三")
        controller.handle_end_dialogue()

        # Assert - 李四（旁听者）被触发学习
        mock_student2.update_knowledge.assert_called_once()

    def test_handle_end_dialogue_with_zero_rounds_does_not_trigger_observer_learning(self):
        """测试零轮对话结束不触发旁听学习"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.update_knowledge = Mock()

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act - 直接结束对话（没有进行任何对话轮）
        controller.handle_end_dialogue()

        # Assert - 旁听学习不被触发（因为对话轮数为0）
        mock_student1.update_knowledge.assert_not_called()


class TestHandleAdvanceCheckpoint:
    """handle_advance_checkpoint 方法测试"""

    def test_handle_advance_checkpoint_clears_active_dialogue(self):
        """测试推进检查点强制结束当前对话"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.update_knowledge = Mock()

        mock_student2 = Mock()
        mock_student2.name = "李四"
        mock_student2.update_knowledge = Mock()

        mock_checkpoint_plan = Mock()
        mock_checkpoint_plan.checkpoints = [
            Mock(title="检查点1", state=CheckpointState.COMPLETE),
            Mock(title="检查点2", state=CheckpointState.TEACHING),
        ]

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=mock_checkpoint_plan,
            ws_push_callback=None
        )

        # 建立对话状态
        controller.handle_teacher_reply("回复张三", "张三")
        assert controller._active_dialogue is not None
        assert controller._dialogue_round_count == 1

        # Act - 推进检查点
        controller.handle_advance_checkpoint()

        # Assert - 对话被强制结束
        assert controller._active_dialogue is None
        assert controller._dialogue_round_count == 0

        # Assert - 旁听学习被触发
        mock_student2.update_knowledge.assert_called_once()

    def test_handle_advance_checkpoint_with_no_active_dialogue(self):
        """测试没有活跃对话时推进检查点不触发旁听学习"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"
        mock_student.update_knowledge = Mock()

        mock_checkpoint_plan = Mock()
        mock_checkpoint_plan.checkpoints = [
            Mock(title="检查点1", state=CheckpointState.COMPLETE),
        ]

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=mock_checkpoint_plan,
            ws_push_callback=None
        )

        # Act - 直接推进检查点（没有活跃对话）
        controller.handle_advance_checkpoint()

        # Assert - 旁听学习不被触发（因为没有对话）
        mock_student.update_knowledge.assert_not_called()


class TestHandleAssignHomework:
    """handle_assign_homework 方法测试"""

    def test_handle_assign_homework_records_to_memory(self):
        """测试布置作业记录到记忆系统"""
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
        homework_content = "完成 Python 列表和元组的练习题"

        # Act
        controller.handle_assign_homework(homework_content)

        # Assert - 作业消息被记录
        messages = mock_memory_manager.session_memory.message_history
        assert len(messages) == 1
        assert messages[0].sender == "teacher"
        assert messages[0].content == homework_content
        assert messages[0].message_type.value == "assign_homework"
        assert messages[0].receiver == "all"
        assert messages[0].timestamp is not None


class TestHandleCollectHomework:
    """handle_collect_homework 方法测试"""

    def test_handle_collect_homework_collects_submissions_from_all_students(self):
        """测试收集所有学生作业提交"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.submit_homework = Mock(return_value="这是我的作业1")

        mock_student2 = Mock()
        mock_student2.name = "李四"
        mock_student2.submit_homework = Mock(return_value="这是我的作业2")

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act
        controller.handle_collect_homework()

        # Assert - 所有学生都被要求提交作业
        mock_student1.submit_homework.assert_called_once()
        mock_student2.submit_homework.assert_called_once()

        # Assert - 作业提交被记录（homework_submission 消息）
        messages = mock_memory_manager.session_memory.message_history
        submission_messages = [m for m in messages if m.message_type.value == "homework_submission"]
        assert len(submission_messages) == 2
        assert submission_messages[0].sender in ["张三", "李四"]
        assert submission_messages[1].sender in ["张三", "李四"]

    def test_handle_collect_homework_with_student_without_submission(self):
        """测试有学生未提交作业时的处理"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"
        mock_student.submit_homework = Mock(return_value=None)  # 未提交

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act
        controller.handle_collect_homework()

        # Assert - 学生被要求提交作业
        mock_student.submit_homework.assert_called_once()

        # Assert - 没有提交消息被记录（因为学生未提交）
        messages = mock_memory_manager.session_memory.message_history
        submission_messages = [m for m in messages if m.message_type.value == "homework_submission"]
        assert len(submission_messages) == 0


class TestHandleEndTeaching:
    """handle_end_teaching 方法测试"""

    def test_handle_end_teaching_collects_feedback_from_all_students(self):
        """测试收集所有学生反馈"""
        # Arrange
        mock_student1 = Mock()
        mock_student1.name = "张三"
        mock_student1.give_feedback = Mock(return_value="这节课讲得很好，我学到了很多")

        mock_student2 = Mock()
        mock_student2.name = "李四"
        mock_student2.give_feedback = Mock(return_value="内容有点难，希望能多讲几遍")

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student1, mock_student2],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act
        result = controller.handle_end_teaching()

        # Assert - 所有学生都被要求提供反馈
        mock_student1.give_feedback.assert_called_once()
        mock_student2.give_feedback.assert_called_once()

        # Assert - 返回值包含所有反馈
        assert "feedbacks" in result
        assert len(result["feedbacks"]) == 2
        assert "这节课讲得很好，我学到了很多" in result["feedbacks"]
        assert "内容有点难，希望能多讲几遍" in result["feedbacks"]

        # Assert - 反馈消息被记录
        messages = mock_memory_manager.session_memory.message_history
        feedback_messages = [m for m in messages if m.message_type.value == "end_feedback"]
        assert len(feedback_messages) == 2
        assert feedback_messages[0].sender in ["张三", "李四"]
        assert feedback_messages[1].sender in ["张三", "李四"]

    def test_handle_end_teaching_with_student_without_feedback(self):
        """测试有学生未提供反馈时的处理"""
        # Arrange
        mock_student = Mock()
        mock_student.name = "张三"
        mock_student.give_feedback = Mock(return_value=None)  # 未提供反馈

        mock_memory_manager = Mock()
        mock_memory_manager.session_memory = Mock()
        mock_memory_manager.session_memory.message_history = []

        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=Mock(),
            ws_push_callback=None
        )

        # Act
        result = controller.handle_end_teaching()

        # Assert - 学生被要求提供反馈
        mock_student.give_feedback.assert_called_once()

        # Assert - 返回值不包含该学生的反馈（None 值被过滤）
        assert "feedbacks" in result
        assert len(result["feedbacks"]) == 0

        # Assert - 没有反馈消息被记录（因为学生未提供反馈）
        messages = mock_memory_manager.session_memory.message_history
        feedback_messages = [m for m in messages if m.message_type.value == "end_feedback"]
        assert len(feedback_messages) == 0


class TestMessageTypeEnums:
    """MessageType 枚举测试"""

    def test_message_type_has_reply_to_student(self):
        """测试 MessageType 包含 REPLY_TO_STUDENT"""
        # Assert - 验证枚举值存在
        assert hasattr(MessageType, "REPLY_TO_STUDENT")
        assert MessageType.REPLY_TO_STUDENT.value == "reply_to_student"






