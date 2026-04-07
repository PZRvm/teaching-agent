"""会话管理 API 集成测试."""


def test_get_messages_empty_session():
    """查询不存在 session 的消息返回空列表."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    response = client.get("/sessions/999/messages")
    assert response.status_code == 200
    assert response.json() == []


def test_get_session_status_not_found():
    """查询不存在的 session 返回 404."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)
    response = client.get("/sessions/999/status")
    assert response.status_code == 404
    assert "detail" in response.json()
