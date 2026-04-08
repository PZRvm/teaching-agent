"""ConnectionManager 单元测试."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.connection_manager import ConnectionManager


class TestConnectionManager:
    """ConnectionManager 单元测试."""

    def test_init_empty(self):
        """初始化时连接池为空."""
        manager = ConnectionManager()
        assert len(manager.active_connections) == 0

    def test_connect_adds_connection(self):
        """connect() 将 WebSocket 添加到指定 session 的连接池."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.connect(session_id=1, websocket=mock_ws)
        assert 1 in manager.active_connections
        assert mock_ws in manager.active_connections[1]

    def test_connect_multiple_sessions(self):
        """不同 session 的连接分开管理."""
        manager = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()
        manager.connect(session_id=1, websocket=ws1)
        manager.connect(session_id=2, websocket=ws2)
        assert ws1 in manager.active_connections[1]
        assert ws2 in manager.active_connections[2]
        assert ws1 not in manager.active_connections[2]

    def test_connect_same_session_multiple_clients(self):
        """同一 session 可以有多个客户端连接."""
        manager = ConnectionManager()
        ws1 = MagicMock()
        ws2 = MagicMock()
        manager.connect(session_id=1, websocket=ws1)
        manager.connect(session_id=1, websocket=ws2)
        assert len(manager.active_connections[1]) == 2

    def test_disconnect_removes_connection(self):
        """disconnect() 从连接池中移除 WebSocket."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.connect(session_id=1, websocket=mock_ws)
        manager.disconnect(session_id=1, websocket=mock_ws)
        # 最后一个连接断开后 key 被删除
        assert 1 not in manager.active_connections

    def test_disconnect_nonexistent_connection(self):
        """断开不存在的连接不报错."""
        manager = ConnectionManager()
        mock_ws = MagicMock()
        manager.disconnect(session_id=999, websocket=mock_ws)

    @pytest.mark.asyncio
    async def test_broadcast_to_session(self):
        """broadcast() 向指定 session 的所有连接发送消息."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.connect(session_id=1, websocket=ws1)
        manager.connect(session_id=1, websocket=ws2)

        message = {"type": "message", "data": "hello"}
        await manager.broadcast(session_id=1, message=message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_empty_session(self):
        """broadcast() 对没有连接的 session 不报错."""
        manager = ConnectionManager()
        message = {"type": "message", "data": "hello"}
        await manager.broadcast(session_id=999, message=message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connection(self):
        """broadcast() 自动移除发送失败的连接."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json.side_effect = Exception("Connection closed")
        manager.connect(session_id=1, websocket=ws1)
        manager.connect(session_id=1, websocket=ws2)

        message = {"type": "message", "data": "hello"}
        await manager.broadcast(session_id=1, message=message)

        assert ws1 in manager.active_connections[1]
        assert ws2 not in manager.active_connections[1]
        assert len(manager.active_connections[1]) == 1

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """send_personal() 向指定连接发送消息."""
        manager = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        manager.connect(session_id=1, websocket=ws1)
        manager.connect(session_id=1, websocket=ws2)

        message = {"type": "message", "data": "private"}
        await manager.send_personal(websocket=ws1, message=message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_personal_dead_connection(self):
        """向已断开的连接发送消息不报错."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection closed")
        await manager.send_personal(websocket=mock_ws, message={"type": "test"})

    def test_get_connection_count(self):
        """get_connection_count() 返回指定 session 的连接数."""
        manager = ConnectionManager()
        assert manager.get_connection_count(session_id=1) == 0
        manager.connect(session_id=1, websocket=MagicMock())
        assert manager.get_connection_count(session_id=1) == 1
        manager.connect(session_id=1, websocket=MagicMock())
        assert manager.get_connection_count(session_id=1) == 2
