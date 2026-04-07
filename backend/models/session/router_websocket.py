"""WebSocket 路由 - 实时双向通信."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


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

    # 发送连接确认
    await websocket.send_json(
        {
            "type": "connected",
            "session_id": session_id,
        }
    )

    logger.info("WebSocket 连接建立 (session_id=%d)", session_id)

    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "pong":
                # 客户端心跳响应，无需处理
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开 (session_id=%d)", session_id)
    except Exception:
        logger.warning("WebSocket 异常 (session_id=%d)", session_id, exc_info=True)
    finally:
        manager.disconnect(session_id=session_id, websocket=websocket)
