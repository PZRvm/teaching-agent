"""WebSocket 连接池管理器."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket

if TYPE_CHECKING:
    pass  # 仅用于类型检查的前向引用

logger = logging.getLogger(__name__)

# 模块级单例（所有模块共享同一个实例）
_connection_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """获取全局 ConnectionManager 单例.

    所有模块（router_websocket、orchestrator、teacher_controller）
    必须使用此函数获取同一个 ConnectionManager 实例，
    否则消息推送将无法到达 WebSocket 客户端。
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def set_connection_manager(cm: ConnectionManager) -> None:
    """设置全局 ConnectionManager 实例（用于测试注入）."""
    global _connection_manager
    _connection_manager = cm


class ConnectionManager:
    """管理所有 WebSocket 连接.

    按 session_id 分组管理连接，支持广播和个人消息。
    自动清理断开的连接。
    """

    def __init__(self) -> None:
        self.active_connections: dict[int, set[WebSocket]] = {}

    def connect(self, session_id: int, websocket: WebSocket) -> None:
        """将 WebSocket 连接添加到指定 session.

        Args:
            session_id: 会话 ID
            websocket: WebSocket 连接实例
        """
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)

    def disconnect(self, session_id: int, websocket: WebSocket) -> None:
        """从连接池中移除 WebSocket.

        Args:
            session_id: 会话 ID
            websocket: WebSocket 连接实例
        """
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, session_id: int, message: dict[str, Any]) -> None:
        """向指定 session 的所有连接广播消息.

        自动移除发送失败的连接。

        Args:
            session_id: 会话 ID
            message: 要发送的消息字典
        """
        if session_id not in self.active_connections:
            return

        dead_connections = []
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                logger.warning("WebSocket 发送失败，移除连接 (session=%d)", session_id)
                dead_connections.append(websocket)

        for ws in dead_connections:
            self.disconnect(session_id, ws)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """向指定 WebSocket 连接发送消息.

        Args:
            websocket: 目标 WebSocket 连接
            message: 要发送的消息字典
        """
        try:
            await websocket.send_json(message)
        except Exception:
            logger.warning("WebSocket 个人消息发送失败")

    def get_connection_count(self, session_id: int) -> int:
        """获取指定 session 的活跃连接数.

        Args:
            session_id: 会话 ID

        Returns:
            活跃连接数
        """
        return len(self.active_connections.get(session_id, set()))
