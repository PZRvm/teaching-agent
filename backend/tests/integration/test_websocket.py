"""WebSocket 端点集成测试."""


def test_websocket_checkpoint_state_change():
    """测试 WebSocket 检查点状态变更事件."""
    import asyncio
    from fastapi.testclient import TestClient
    from main import app

    async def test():
        with TestClient(app) as client:
            with client.websocket_connect("/ws/sessions/1") as websocket:
                # 接收连接确认消息
                data = websocket.receive_json()
                assert data["type"] == "connected"

                # 接收检查点状态变更
                data = websocket.receive_json()
                assert data["type"] == "checkpoint_state_change"
                assert "data" in data

    asyncio.run(test())
