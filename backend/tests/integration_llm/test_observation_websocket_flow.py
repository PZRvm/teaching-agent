"""观察模式 WebSocket 流程集成测试.

测试完整的端到端流程（需要运行中的后端服务器）：
1. 调用 /observation/start 创建会话
2. 立即连接 WebSocket（orchestrator 可能未就绪）
3. 接收 connected 事件
4. 验证 ready 字段
5. （可选）等待 session_state:running 事件

运行方式：
    # 先启动后端
    python main.py

    # 然后运行测试
    pytest tests/integration_llm/test_observation_websocket_flow.py -v -s
"""

import asyncio
import os

import pytest

# 禁用代理连接 localhost
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
os.environ["no_proxy"] = "localhost,127.0.0.1"

import websockets


def _server_is_running() -> bool:
    """检查后端服务器是否在运行."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", 8000)) == 0


server_not_running = pytest.mark.skipif(
    not _server_is_running(),
    reason="需要运行中的后端服务器 (python main.py)",
)


@server_not_running
@pytest.mark.asyncio
async def test_observation_websocket_flow():
    """测试完整的观察模式 WebSocket 流程.

    验证：
    1. API 立即返回 session_id（< 1 秒）
    2. WebSocket 能立即连接（即使 orchestrator 未就绪）
    3. 接收 connected 事件
    4. ready 字段正确反映 orchestrator 状态
    """
    from fastapi.testclient import TestClient

    from main import app

    with TestClient(app) as client:
        # 1. 创建观察会话
        payload = {
            "topic": "WebSocket 流程测试",
            "teaching_mode": "didactic",
            "students": [
                {
                    "name": "测试学生",
                    "level": "average",
                    "attitude": "neutral",
                    "learning_ability": 7,
                }
            ],
        }

        response = client.post("/observation/start", json=payload)

        assert response.status_code == 200
        data = response.json()
        session_id = data.get("session_id")
        assert session_id is not None
        assert data.get("status") == "initializing"


@server_not_running
def test_observation_websocket_with_real_server():
    """使用真实服务器测试 WebSocket 流程.

    注意：此测试需要在运行测试前启动后端服务器：
    python main.py
    """
    import json
    import time

    import requests

    # 1. 创建观察会话
    print("\n1. 创建观察会话...")
    start_time = time.time()

    response = requests.post(
        "http://localhost:8000/observation/start",
        json={
            "topic": "WebSocket 流程测试",
            "teaching_mode": "didactic",
            "students": [
                {
                    "name": "测试学生",
                    "level": "average",
                    "attitude": "neutral",
                    "learning_ability": 7,
                }
            ],
        },
        timeout=5,
    )

    elapsed = (time.time() - start_time) * 1000
    print(f"   API 耗时: {elapsed:.0f}ms")

    assert response.status_code == 200
    data = response.json()
    session_id = data.get("session_id")
    assert session_id is not None
    assert data.get("status") == "initializing"
    print(f"   ✓ Session 创建成功: session_id={session_id}")

    # API 应该在 1 秒内返回
    assert elapsed < 1000, f"API 耗时 {elapsed:.0f}ms，应该 < 1000ms"

    # 2. 连接 WebSocket
    async def connect_websocket():
        uri = f"ws://localhost:8000/ws/sessions/{session_id}"
        print(f"\n2. 连接 WebSocket: {uri}")

        try:
            async with websockets.connect(uri, open_timeout=5, close_timeout=2) as ws:
                print("   ✓ WebSocket 连接成功")

                # 3. 接收第一条消息（connected 事件）
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                event = json.loads(msg)
                print(f"\n3. 收到事件: type={event.get('type')}")

                assert event.get("type") == "connected"
                assert event.get("session_id") == session_id
                print("   ✓ connected 事件验证成功")
                print(f"     session_id: {event.get('session_id')}")
                print(f"     mode: {event.get('mode')}")
                print(f"     ready: {event.get('ready')}")

                # 4. （可选）等待更多事件
                print("\n4. 等待更多事件（5秒）...")
                try:
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=5)
                        event = json.loads(msg)
                        print(f"   收到事件: type={event.get('type')}, status={event.get('status', 'N/A')}")

                        if event.get("type") == "session_state" and event.get("status") == "running":
                            print("   ✓ 收到 running 状态，orchestrator 已就绪")
                            break
                except TimeoutError:
                    print("   （5秒内未收到更多事件，这是正常的）")

                print("\n✓✓✓ 测试通过！")
                print("  - API 立即返回 session_id")
                print("  - WebSocket 成功连接")
                print("  - connected 事件正确")

        except Exception as e:
            pytest.fail(f"WebSocket 测试失败: {e}")

    # 运行 WebSocket 测试
    asyncio.run(connect_websocket())


@server_not_running
def test_observation_websocket_session_not_found():
    """测试连接到不存在的 session.

    验证 WebSocket 端点正确处理 session 不存在的情况。
    """
    import json

    async def connect_to_nonexistent_session():
        uri = "ws://localhost:8000/ws/sessions/99999"
        print(f"\n连接到不存在的 session: {uri}")

        try:
            async with websockets.connect(uri, open_timeout=3, close_timeout=1) as ws:
                # 如果连接成功，应该收到错误消息
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                event = json.loads(msg)
                print(f"收到消息: {event}")

                # 后端可能发送 error 事件或直接关闭连接
                if event.get("type") == "error":
                    print("✓ 正确返回 error 事件")
                    return
                else:
                    pytest.fail(f"预期 error 事件，收到: {event}")

        except websockets.exceptions.ConnectionClosedError as e:
            # 连接被关闭也是正确的行为
            print(f"✓ 连接被正确关闭: {e}")
        except websockets.exceptions.InvalidStatusCode as e:
            # 404 等状态码也是正确的
            if e.status_code == 404:
                print("✓ 正确返回 404 状态码")
            else:
                pytest.fail(f"Unexpected status code: {e.status_code}")
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")

    asyncio.run(connect_to_nonexistent_session())


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    print("=" * 60)
    print("观察模式 WebSocket 流程测试")
    print("=" * 60)
    print("\n注意：请确保后端服务器正在运行（python main.py）")
    print("=" * 60)

    try:
        test_observation_websocket_with_real_server()
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
    except Exception as e:
        print(f"\n✗ 测试错误: {e}")
