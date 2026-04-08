"""WebSocket 端点集成测试."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(autouse=True)
def reset_globals():
    """每个测试前重置全局状态."""
    from core.connection_manager import ConnectionManager, set_connection_manager
    from core.session_registry import SessionRegistry

    from models.session.router_websocket import set_session_registry

    set_connection_manager(ConnectionManager())
    set_session_registry(SessionRegistry())


class TestWebSocketConnection:
    """WebSocket 连接测试."""

    def test_websocket_connect_and_receive_connected_event(self):
        """WebSocket 连接后收到 connected 事件."""
        with TestClient(app) as client, client.websocket_connect("/ws/sessions/1") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["session_id"] == 1

    def test_websocket_ping_pong(self):
        """WebSocket ping/pong 心跳机制."""
        with TestClient(app) as client, client.websocket_connect("/ws/sessions/1") as websocket:
            # 跳过 connected 事件
            websocket.receive_json()

            # 发送 ping
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"

    def test_websocket_disconnect_handling(self):
        """WebSocket 客户端断开时服务端不崩溃."""
        # 使用嵌套 with 确保断开时 TestClient 仍存活
        with TestClient(app) as client, client.websocket_connect("/ws/sessions/1") as websocket:
            websocket.receive_json()  # connected
        # 退出 with 块后，连接已断开，无异常


class TestWebSocketCommandIntegration:
    """WebSocket 命令路由集成测试."""

    def test_broadcast_lecture_command_via_websocket(self):
        """通过 WebSocket 发送 broadcast_lecture 命令，controller 被调用."""
        from models.session.router_websocket import get_session_registry

        mock_controller = MagicMock()
        mock_controller.handle_broadcast_lecture = MagicMock()

        registry = get_session_registry()
        registry.register(session_id=42, mode="teacher", controller=mock_controller)

        with TestClient(app) as client, client.websocket_connect("/ws/sessions/42") as websocket:
            # 接收 connected 事件
            data = websocket.receive_json()
            assert data["type"] == "connected"

            # 发送命令
            websocket.send_json({
                "type": "broadcast_lecture",
                "content": "测试讲授内容",
            })

            # 接收命令结果
            result = websocket.receive_json()
            assert result["type"] == "command_result"
            assert result["command"] == "broadcast_lecture"
            assert result["success"] is True

        # 验证 controller 被调用
        mock_controller.handle_broadcast_lecture.assert_called_once_with("测试讲授内容")

    def test_unknown_command_returns_error_via_websocket(self):
        """发送未知命令类型时返回 error."""
        from models.session.router_websocket import get_session_registry

        mock_controller = MagicMock()
        registry = get_session_registry()
        registry.register(session_id=43, mode="teacher", controller=mock_controller)

        with TestClient(app) as client, client.websocket_connect("/ws/sessions/43") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

            websocket.send_json({"type": "invalid_command"})

            result = websocket.receive_json()
            assert result["type"] == "error"
            assert "unknown command" in result["message"].lower()

    def test_command_to_nonexistent_session_returns_error(self):
        """向未注册的 session 发送命令返回 error."""
        with TestClient(app) as client, client.websocket_connect("/ws/sessions/999") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

            websocket.send_json({
                "type": "broadcast_lecture",
                "content": "测试",
            })

            result = websocket.receive_json()
            assert result["type"] == "error"
            assert "not found" in result["message"].lower()

    def test_observation_mode_rejects_commands(self):
        """观察模式会话拒绝教师命令."""
        from models.session.router_websocket import get_session_registry

        mock_orchestrator = MagicMock()
        registry = get_session_registry()
        registry.register(session_id=44, mode="observation", orchestrator=mock_orchestrator)

        with TestClient(app) as client, client.websocket_connect("/ws/sessions/44") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"

            websocket.send_json({
                "type": "broadcast_lecture",
                "content": "测试",
            })

            result = websocket.receive_json()
            assert result["type"] == "error"
            assert "observation mode" in result["message"].lower()
