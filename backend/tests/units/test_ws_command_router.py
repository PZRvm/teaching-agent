"""WebSocket 命令 schema 测试和命令路由测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError


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


class TestWsCommandRouter:
    """WebSocket 端点命令路由测试."""

    @pytest.mark.asyncio
    async def test_broadcast_lecture_routes_to_controller(self):
        """broadcast_lecture 命令路由到 TeacherSessionController.handle_broadcast_lecture."""
        mock_controller = MagicMock()
        mock_controller.handle_broadcast_lecture = MagicMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(
                AsyncMock(), 1, {"type": "broadcast_lecture", "content": "测试讲授"}
            )

            mock_controller.handle_broadcast_lecture.assert_called_once_with("测试讲授")

    @pytest.mark.asyncio
    async def test_ask_to_all_routes_to_controller(self):
        """ask_to_all 命令路由到 TeacherSessionController.handle_ask_to_all."""
        mock_controller = MagicMock()
        mock_controller.handle_ask_to_all = MagicMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(
                AsyncMock(), 1, {"type": "ask_to_all", "question": "什么是变量？"}
            )

            mock_controller.handle_ask_to_all.assert_called_once_with("什么是变量？")

    @pytest.mark.asyncio
    async def test_unknown_command_returns_error(self):
        """未知命令类型返回 error 响应."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = MagicMock()
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(mock_ws, 1, {"type": "nonexistent"})

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "error"
            assert "unknown command" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_no_session_returns_error(self):
        """session 不存在时返回 error 响应."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = None
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(mock_ws, 1, {"type": "broadcast_lecture", "content": "测试"})

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "error"
            assert "not found" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_advance_checkpoint_routes_to_controller(self):
        """advance_checkpoint 命令路由到 TeacherSessionController.handle_advance_checkpoint."""
        mock_controller = MagicMock()
        mock_controller.handle_advance_checkpoint = MagicMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(AsyncMock(), 1, {"type": "advance_checkpoint"})

            mock_controller.handle_advance_checkpoint.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_result_pushed_via_websocket(self):
        """命令执行结果通过 WebSocket 推送回客户端."""
        mock_controller = MagicMock()
        mock_controller.handle_broadcast_lecture = MagicMock()

        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(mock_ws, 1, {"type": "broadcast_lecture", "content": "测试"})

            # 验证发送了成功响应
            mock_ws.send_json.assert_called()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "command_result"
            assert call_args["command"] == "broadcast_lecture"
            assert call_args["success"] is True

    @pytest.mark.asyncio
    async def test_end_dialogue_routes_to_controller(self):
        """end_dialogue 命令路由到 TeacherSessionController.handle_end_dialogue."""
        mock_controller = MagicMock()
        mock_controller.handle_end_dialogue = MagicMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(AsyncMock(), 1, {"type": "end_dialogue"})

            mock_controller.handle_end_dialogue.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_homework_routes_to_controller(self):
        """assign_homework 命令路由到 TeacherSessionController.handle_assign_homework."""
        mock_controller = MagicMock()
        mock_controller.handle_assign_homework = MagicMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(
                AsyncMock(), 1, {"type": "assign_homework", "content": "完成作业"}
            )

            mock_controller.handle_assign_homework.assert_called_once_with("完成作业")

    @pytest.mark.asyncio
    async def test_collect_homework_routes_to_controller(self):
        """collect_homework 命令路由到 TeacherSessionController.handle_collect_homework."""
        mock_controller = MagicMock()
        mock_controller.handle_collect_homework = MagicMock()

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(
                AsyncMock(), 1, {"type": "collect_homework", "homework_prompt": "练习1"}
            )

            mock_controller.handle_collect_homework.assert_called_once_with("练习1")

    @pytest.mark.asyncio
    async def test_end_teaching_routes_to_controller(self):
        """end_teaching 命令路由到 TeacherSessionController.handle_end_teaching."""
        mock_controller = MagicMock()
        mock_controller.handle_end_teaching = MagicMock(return_value={"feedbacks": []})

        with patch("models.session.services.websocket_handlers.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.services.websocket_handlers import handle_command

            await handle_command(AsyncMock(), 1, {"type": "end_teaching"})

            mock_controller.handle_end_teaching.assert_called_once()
