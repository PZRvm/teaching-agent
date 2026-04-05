"""WebSocket 路由 - 检查点状态变更推送."""

from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def websocket_checkpoint_updates(websocket: WebSocket, session_id: int):
    """WebSocket 端点：推送检查点状态变更."""
    await websocket.accept()

    # 发送连接确认消息
    await websocket.send_json({"type": "connected"})

    # 发送检查点状态变更（模拟）
    await websocket.send_json(
        {
            "type": "checkpoint_state_change",
            "data": {"session_id": session_id, "checkpoint_index": 0, "state": "teaching"},
        }
    )
