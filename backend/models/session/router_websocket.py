"""WebSocket 路由 - 实时双向通信."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.connection_manager import get_connection_manager
from core.session_registry import get_session_registry, set_session_registry
from models.session.services.websocket_handlers import TEACHER_COMMAND_HANDLERS, handle_command

logger = logging.getLogger(__name__)

router = APIRouter()

# 向后兼容：外部代码可能从 router_websocket 导入这些函数
# 实际实现在 core.session_registry 模块
__all__ = ["router", "get_session_registry", "set_session_registry"]


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: int):
    """WebSocket 端点：实时双向通信.

    支持：
    - 观察模式：接收后端推送的教学消息和检查点状态
    - 教师模式：接收用户操作指令，推送学生响应
    - 心跳：ping/pong 保活
    """
    await websocket.accept()

    # 注册连接（使用共享单例）
    manager = get_connection_manager()
    manager.connect(session_id=session_id, websocket=websocket)

    logger.info("WebSocket 连接建立 (session_id=%d)", session_id)

    try:
        # 检查会话是否已注册且 orchestrator 是否就绪
        registry = get_session_registry()
        logger.debug("当前注册的会话: %s", session_id)
        session_info = registry.get_session_info(session_id)

        if session_info is None:
            # 会话不存在，发送错误并关闭连接
            logger.warning("WebSocket 连接请求的会话不存在 (session_id=%d)", session_id)
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"Session {session_id} not found",
                    "session_id": session_id,
                }
            )
            await websocket.close(code=1008, reason="Session not found")
            return

        # 发送连接确认和当前会话状态
        mode = session_info["mode"]
        orchestrator = registry.get_orchestrator(session_id) if mode == "observation" else None
        logger.info("发送 connected 事件 (session_id=%d, mode=%s, ready=%s)", session_id, mode, orchestrator is not None)

        await websocket.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "mode": mode,
                "ready": orchestrator is not None,
            }
        )

        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "pong":
                pass  # 客户端心跳响应
            elif msg_type in TEACHER_COMMAND_HANDLERS:
                # 路由到命令处理器
                await handle_command(websocket, session_id, data)
            elif msg_type:
                # 未知命令类型
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Unknown command: {msg_type}",
                        "session_id": session_id,
                    }
                )

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开 (session_id=%d)", session_id)
    except Exception:
        logger.warning("WebSocket 异常 (session_id=%d)", session_id, exc_info=True)
    finally:
        manager.disconnect(session_id=session_id, websocket=websocket)
