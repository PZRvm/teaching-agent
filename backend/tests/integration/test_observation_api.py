"""观察模式 API 集成测试."""


def test_start_observation_creates_session():
    """启动观察模式创建 teaching_session 记录."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    payload = {
        "topic": "Python Basics",
        "teaching_mode": "heuristic",
        "checkpoint_count": 3,
        "students": [
            {
                "name": "Student1",
                "level": "average",
                "attitude": "neutral",
                "learning_ability": 5,
            },
        ],
    }

    response = client.post("/observation/start", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert isinstance(data["session_id"], int)
    assert data["status"] == "running"
    assert data["session_id"] > 0


def test_start_observation_missing_topic():
    """缺少 topic 参数返回 422."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    payload = {
        "teaching_mode": "heuristic",
        "students": [
            {"name": "Student1", "level": "average", "attitude": "neutral", "learning_ability": 5}
        ],
    }
    response = client.post("/observation/start", json=payload)
    assert response.status_code == 422


def test_start_observation_empty_students():
    """空学生列表返回 422."""
    from fastapi.testclient import TestClient

    from main import app

    client = TestClient(app)

    payload = {
        "topic": "Python Basics",
        "teaching_mode": "heuristic",
        "students": [],
    }
    response = client.post("/observation/start", json=payload)
    assert response.status_code == 422
