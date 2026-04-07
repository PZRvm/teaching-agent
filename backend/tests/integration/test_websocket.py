"""WebSocket 端点集成测试."""

from fastapi.testclient import TestClient

from main import app


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

    def test_websocket_unknown_message_type_ignored(self):
        """未知消息类型被忽略，不断开连接."""
        with TestClient(app) as client, client.websocket_connect("/ws/sessions/1") as websocket:
            websocket.receive_json()  # connected
            websocket.send_json({"type": "unknown_type"})
            # 连接仍然存活，可以继续发送 ping
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"
