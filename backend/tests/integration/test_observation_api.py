"""观察模式 API 集成测试."""


def test_start_observation_session():
    """测试启动观察模式会话."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    response = client.post(
        "/observation/start",
        json={
            "topic": "Python Basics",
            "teaching_mode": "heuristic",
            "checkpoint_count": 3,
            "students": [
                {
                    "name": "Student1",
                    "level": "average",
                    "attitude": "neutral",
                    "learning_ability": 5,
                }
            ]
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "running"
