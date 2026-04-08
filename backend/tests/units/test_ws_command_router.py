"""WebSocket 命令 schema 测试."""

from pydantic import ValidationError

import pytest


class TestWsCommandSchemas:
    """WebSocket 命令 schema 验证测试."""

    def test_broadcast_lecture_command_valid(self):
        """合法的 broadcast_lecture 命令."""
        from models.session.schemas import WsBroadcastLectureCommand

        cmd = WsBroadcastLectureCommand(content="今天我们学习 Python 变量")
        assert cmd.type == "broadcast_lecture"
        assert cmd.content == "今天我们学习 Python 变量"

    def test_broadcast_lecture_command_missing_content(self):
        """缺少 content 字段应报错."""
        from models.session.schemas import WsBroadcastLectureCommand

        with pytest.raises(ValidationError):
            WsBroadcastLectureCommand(type="broadcast_lecture")

    def test_ask_to_all_command_valid(self):
        """合法的 ask_to_all 命令."""
        from models.session.schemas import WsAskToAllCommand

        cmd = WsAskToAllCommand(question="什么是变量？")
        assert cmd.type == "ask_to_all"
        assert cmd.question == "什么是变量？"

    def test_ask_to_all_command_missing_question(self):
        """缺少 question 字段应报错."""
        from models.session.schemas import WsAskToAllCommand

        with pytest.raises(ValidationError):
            WsAskToAllCommand(type="ask_to_all")

    def test_ask_to_student_command_valid(self):
        """合法的 ask_to_student 命令."""
        from models.session.schemas import WsAskToStudentCommand

        cmd = WsAskToStudentCommand(question="什么是变量？", student_name="张三")
        assert cmd.type == "ask_to_student"
        assert cmd.student_name == "张三"

    def test_ask_to_student_command_missing_fields(self):
        """缺少 student_name 字段应报错."""
        from models.session.schemas import WsAskToStudentCommand

        with pytest.raises(ValidationError):
            WsAskToStudentCommand(type="ask_to_student", question="测试")

    def test_teacher_reply_command_valid(self):
        """合法的 teacher_reply 命令."""
        from models.session.schemas import WsTeacherReplyCommand

        cmd = WsTeacherReplyCommand(reply="回答正确", student_name="张三")
        assert cmd.type == "teacher_reply"
        assert cmd.student_name == "张三"

    def test_advance_checkpoint_command_valid(self):
        """合法的 advance_checkpoint 命令."""
        from models.session.schemas import WsAdvanceCheckpointCommand

        cmd = WsAdvanceCheckpointCommand()
        assert cmd.type == "advance_checkpoint"

    def test_end_dialogue_command_valid(self):
        """合法的 end_dialogue 命令."""
        from models.session.schemas import WsEndDialogueCommand

        cmd = WsEndDialogueCommand()
        assert cmd.type == "end_dialogue"

    def test_assign_homework_command_valid(self):
        """合法的 assign_homework 命令."""
        from models.session.schemas import WsAssignHomeworkCommand

        cmd = WsAssignHomeworkCommand(content="完成课后作业")
        assert cmd.type == "assign_homework"
        assert cmd.content == "完成课后作业"

    def test_collect_homework_command_valid(self):
        """合法的 collect_homework 命令."""
        from models.session.schemas import WsCollectHomeworkCommand

        cmd = WsCollectHomeworkCommand(homework_prompt="完成练习1和练习2")
        assert cmd.type == "collect_homework"

    def test_end_teaching_command_valid(self):
        """合法的 end_teaching 命令."""
        from models.session.schemas import WsEndTeachingCommand

        cmd = WsEndTeachingCommand()
        assert cmd.type == "end_teaching"

    def test_unknown_command_type_rejected(self):
        """未知命令类型应报错."""
        from models.session.schemas import WsTeacherCommand

        with pytest.raises(ValidationError):
            WsTeacherCommand(type="unknown_command")
