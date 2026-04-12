"""WebSocket 命令处理器 — 处理教师模式的客户端命令."""

import logging
from typing import Any

from fastapi import WebSocket
from pydantic import ValidationError

from core.session_registry import SessionRegistry, get_session_registry
from models.session.schemas import (
    WsAskToAllCommand,
    WsAskToStudentCommand,
    WsAssignHomeworkCommand,
    WsBroadcastLectureCommand,
    WsCollectHomeworkCommand,
    WsTeacherReplyCommand,
)

logger = logging.getLogger(__name__)

# 教师模式命令映射
TEACHER_COMMAND_HANDLERS: dict[str, str] = {
    "broadcast_lecture": "_handle_broadcast_lecture",
    "ask_to_all": "_handle_ask_to_all",
    "ask_to_student": "_handle_ask_to_student",
    "teacher_reply": "_handle_teacher_reply",
    "advance_checkpoint": "_handle_advance_checkpoint",
    "end_dialogue": "_handle_end_dialogue",
    "assign_homework": "_handle_assign_homework",
    "collect_homework": "_handle_collect_homework",
    "end_teaching": "_handle_end_teaching",
}


async def handle_command(websocket: WebSocket, session_id: int, data: dict[str, Any]) -> None:
    """处理 WebSocket 命令并路由到对应的 handler.

    Args:
        websocket: WebSocket 连接实例
        session_id: 会话 ID
        data: 接收到的 JSON 数据
    """
    registry = get_session_registry()

    session_info = registry.get_session_info(session_id)

    if session_info is None:
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Session {session_id} not found",
                "session_id": session_id,
            }
        )
        return

    mode = session_info["mode"]
    command_type = data.get("type", "")

    if mode == "teacher":
        await _handle_teacher_command(websocket, session_id, command_type, data, registry)
    else:
        # 观察模式：当前 orchestrator 自动运行，WebSocket 只接收观察命令
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Observation mode does not support command '{command_type}'",
                "session_id": session_id,
            }
        )


async def _handle_teacher_command(
    websocket: WebSocket,
    session_id: int,
    command_type: str,
    data: dict[str, Any],
    registry: SessionRegistry,
) -> None:
    """处理教师模式命令."""
    controller = registry.get_controller(session_id)
    if controller is None:
        await websocket.send_json(
            {
                "type": "error",
                "message": f"No controller for session {session_id}",
                "session_id": session_id,
            }
        )
        return

    handler_name = TEACHER_COMMAND_HANDLERS.get(command_type)
    if handler_name is None:
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Unknown command: {command_type}",
                "session_id": session_id,
            }
        )
        return

    try:
        await getattr(TeacherCommandHandlers, handler_name)(
            websocket, session_id, data, controller
        )
    except ValidationError as e:
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Invalid command data: {e}",
                "command": command_type,
                "session_id": session_id,
            }
        )
    except Exception as e:
        logger.error("Command '%s' failed: %s", command_type, e, exc_info=True)
        await websocket.send_json(
            {
                "type": "error",
                "message": f"Command '{command_type}' failed: {e}",
                "command": command_type,
                "session_id": session_id,
            }
        )


class TeacherCommandHandlers:
    """教师模式命令处理器（静态方法集合）."""

    @staticmethod
    async def _handle_broadcast_lecture(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsBroadcastLectureCommand(**data)
        controller.handle_broadcast_lecture(cmd.content)
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "broadcast_lecture",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_ask_to_all(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsAskToAllCommand(**data)
        controller.handle_ask_to_all(cmd.question)
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "ask_to_all",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_ask_to_student(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsAskToStudentCommand(**data)
        result = controller.handle_ask_to_student(cmd.question, cmd.student_name)
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "ask_to_student",
                "success": True,
                "session_id": session_id,
                "data": result,
            }
        )

    @staticmethod
    async def _handle_teacher_reply(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsTeacherReplyCommand(**data)
        controller.handle_teacher_reply(cmd.reply, cmd.student_name)
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "teacher_reply",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_advance_checkpoint(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        controller.handle_advance_checkpoint()
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "advance_checkpoint",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_end_dialogue(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        controller.handle_end_dialogue()
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "end_dialogue",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_assign_homework(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsAssignHomeworkCommand(**data)
        controller.handle_assign_homework(cmd.content)
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "assign_homework",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_collect_homework(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsCollectHomeworkCommand(**data)
        controller.handle_collect_homework(cmd.homework_prompt)
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "collect_homework",
                "success": True,
                "session_id": session_id,
            }
        )

    @staticmethod
    async def _handle_end_teaching(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        controller.handle_end_teaching()
        await websocket.send_json(
            {
                "type": "command_result",
                "command": "end_teaching",
                "success": True,
                "session_id": session_id,
            }
        )
