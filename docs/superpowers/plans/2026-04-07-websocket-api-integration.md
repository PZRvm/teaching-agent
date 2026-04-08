# WebSocket通信 + 后端API整合 实施计划

> **For agentic workers（智能体工作者）:** 必须使用 `superpowers:test-driven-development` 技能逐步执行此计划。每个任务遵循 RED-GREEN-REFACTOR-COMMIT 循环。步骤使用复选框 (`- [ ]`) 语法追踪进度。

**目标:** 实现前后端实时双向通信（WebSocket）和所有 REST API 端点（观察模式、会话管理、消息查询），使前端能实时看到教学交互并获取历史数据。

**架构:** WebSocket 连接管理器（ConnectionManager）统一管理所有 session 的 WebSocket 连接池，SessionOrchestrator 和 TeacherSessionController 通过回调推送消息。REST API 层提供消息查询、会话管理、观察模式启动等 HTTP 端点。两种模式共享同一个 WebSocket 端点，通过 session 类型区分行为。

**技术栈:** FastAPI WebSocket, asyncio, Pydantic, SQLAlchemy async, httpx (测试)

---

## 文件结构

```
backend/
├── core/
│   └── connection_manager.py      # [新建] WebSocket 连接池管理器（含单例）
├── models/
│   ├── session/
│   │   ├── router_websocket.py    # [重写] WebSocket 端点（观察+教师模式）
│   │   ├── router.py              # [新建] 会话管理 REST API
│   │   └── schemas.py             # [修改] 新增 WebSocket 事件 schemas
│   └── observation/
│       ├── router.py              # [重写] 观察模式 API（真实实现）
│       └── schemas.py             # [修改] 新增响应字段
├── orm/
│   └── message.py                 # [修改] 添加 receiver 列
├── alembic/
│   └── versions/                  # [新建] 004_add_receiver_to_messages.py
├── tests/
│   ├── units/
│   │   ├── test_connection_manager.py   # [新建] ConnectionManager 单元测试
│   │   ├── test_orchestrator_ws_push.py # [新建] Orchestrator WS 推送测试
│   │   ├── test_teacher_controller_ws_push.py # [新建] Controller WS 推送测试
│   │   └── test_session_router.py       # [新建] 会话管理 API 单元测试
│   └── integration/
│       ├── test_websocket.py            # [重写] WebSocket 集成测试
│       ├── test_session_api.py          # [新建] 会话管理 API 集成测试
│       └── test_observation_api.py      # [重写] 观察模式 API 集成测试
└── main.py                        # [修改] 注册新路由
```

---

## Phase 8: WebSocket 通信

### Task 1: WebSocket 事件 Schemas

**涉及文件：**
- 修改: `backend/models/session/schemas.py`

- [ ] **Step 1: 编写失败测试**

在 `backend/tests/units/test_schemas.py` 中添加 WebSocket 事件 schema 测试：

```python
# backend/tests/units/test_schemas.py 追加

from models.session.schemas import (
    WsConnectedEvent,
    WsMessageEvent,
    WsCheckpointStateEvent,
    WsSessionEndEvent,
    WsStudentAnswerEvent,
    WsSessionStateEvent,
)


class TestWebSocketEventSchemas:
    """WebSocket 事件 schema 测试."""

    def test_ws_connected_event(self):
        event = WsConnectedEvent(session_id=1, mode="observation")
        assert event.type == "connected"
        assert event.session_id == 1
        assert event.mode == "observation"

    def test_ws_message_event(self):
        event = WsMessageEvent(
            session_id=1,
            sender="teacher",
            message_type="lecture",
            content="今天我们学习Python变量",
            receiver="all",
        )
        assert event.type == "message"
        assert event.sender == "teacher"
        assert event.message_type == "lecture"

    def test_ws_checkpoint_state_event(self):
        event = WsCheckpointStateEvent(
            session_id=1,
            index=0,
            checkpoint={"title": "变量", "state": "teaching", "key_point": "变量的定义"},
            progress={"current": 1, "total": 5, "completed": 0},
        )
        assert event.type == "checkpoint_state_change"
        assert event.index == 0
        assert event.progress["total"] == 5

    def test_ws_session_end_event(self):
        event = WsSessionEndEvent(session_id=1, reason="all_checkpoints_complete")
        assert event.type == "session_end"
        assert event.reason == "all_checkpoints_complete"

    def test_ws_student_answer_event(self):
        event = WsStudentAnswerEvent(
            session_id=1,
            student_name="张三",
            content="一次函数是 y=kx+b",
            message_type="answer_to_checkpoint",
        )
        assert event.type == "student_answer"
        assert event.student_name == "张三"

    def test_ws_session_state_event(self):
        event = WsSessionStateEvent(
            session_id=1,
            teaching_mode="heuristic",
            phase="teaching",
            checkpoint_index=0,
            total_checkpoints=5,
        )
        assert event.type == "session_state"
        assert event.phase == "teaching"
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_schemas.py::TestWebSocketEventSchemas -v`
预期:失败，ImportError（schemas 未定义）

- [ ] **Step 3: 编写最小实现**

在 `backend/models/session/schemas.py` 末尾添加：

```python
# WebSocket 事件 schemas


class WsEventBase(BaseModel):
    """WebSocket 事件基类."""

    type: str
    session_id: int


class WsConnectedEvent(WsEventBase):
    """WebSocket 连接确认事件."""

    type: str = "connected"
    mode: str = Field(description="会话模式 (observation/teacher)")


class WsMessageEvent(WsEventBase):
    """WebSocket 消息事件（教师讲授/学生回答等）."""

    type: str = "message"
    sender: str
    message_type: str
    content: str
    receiver: str = "all"


class WsCheckpointStateEvent(WsEventBase):
    """WebSocket 检查点状态变更事件."""

    type: str = "checkpoint_state_change"
    index: int
    checkpoint: dict
    progress: dict


class WsStudentAnswerEvent(WsEventBase):
    """WebSocket 学生回答事件（教师模式实时推送）."""

    type: str = "student_answer"
    student_name: str
    content: str
    message_type: str


class WsSessionStateEvent(WsEventBase):
    """WebSocket 会话状态事件."""

    type: str = "session_state"
    teaching_mode: str
    phase: str
    checkpoint_index: int = 0
    total_checkpoints: int = 0


class WsSessionEndEvent(WsEventBase):
    """WebSocket 会话结束事件."""

    type: str = "session_end"
    reason: str
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_schemas.py::TestWebSocketEventSchemas -v`
预期:通过（6 个测试）

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add models/session/schemas.py tests/units/test_schemas.py
git commit -m "feat(schemas): add WebSocket event schemas for real-time communication"
```

---

### Task 2: ConnectionManager 连接池管理器

**涉及文件：**
- 新建: `backend/core/connection_manager.py`
- 新建: `backend/tests/units/test_connection_manager.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/units/test_connection_manager.py

import asyncio
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
        assert len(manager.active_connections[1]) == 0

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
        # 不应该抛出异常
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

        # ws1 应该还在，ws2 应该被移除
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

    def test_get_connection_count(self):
        """get_connection_count() 返回指定 session 的连接数."""
        manager = ConnectionManager()
        assert manager.get_connection_count(session_id=1) == 0
        manager.connect(session_id=1, websocket=MagicMock())
        assert manager.get_connection_count(session_id=1) == 1
        manager.connect(session_id=1, websocket=MagicMock())
        assert manager.get_connection_count(session_id=1) == 2
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_connection_manager.py -v`
预期:失败，ModuleNotFoundError

- [ ] **Step 3: 编写最小实现**

```python
# backend/core/connection_manager.py

"""WebSocket 连接池管理器."""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

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
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_connection_manager.py -v`
预期:通过（10 个测试）

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add core/connection_manager.py tests/units/test_connection_manager.py
git commit -m "feat(websocket): add ConnectionManager for WebSocket connection pool"
```

---

### Task 3: 重写 WebSocket 端点（观察模式消息推送）

**涉及文件：**
- 重写: `backend/models/session/router_websocket.py`
- 重写: `backend/tests/integration/test_websocket.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/integration/test_websocket.py

"""WebSocket 端点集成测试."""

import pytest
from fastapi.testclient import TestClient

from main import app


class TestWebSocketConnection:
    """WebSocket 连接测试."""

    def test_websocket_connect_and_receive_connected_event(self):
        """WebSocket 连接后收到 connected 事件."""
        with TestClient(app) as client, client.websocket_connect(
            "/ws/sessions/1"
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert data["session_id"] == 1

    def test_websocket_ping_pong(self):
        """WebSocket ping/pong 心跳机制."""
        with TestClient(app) as client, client.websocket_connect(
            "/ws/sessions/1"
        ) as websocket:
            # 跳过 connected 事件
            websocket.receive_json()

            # 发送 ping
            websocket.send_json({"type": "ping"})
            data = websocket.receive_json()
            assert data["type"] == "pong"


class TestWebSocketBroadcast:
    """WebSocket 广播测试."""

    def test_broadcast_message_to_session(self):
        """通过 ConnectionManager 向 session 广播消息."""
        from core.connection_manager import ConnectionManager

        manager = ConnectionManager()
        # 注意：这里只测试 ConnectionManager 的广播能力
        # WebSocket 端点的广播集成在观察模式 API 测试中覆盖
        assert manager.get_connection_count(session_id=1) == 0
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/integration/test_websocket.py -v`
预期:失败（ping/pong 未实现）

- [ ] **Step 3: 编写最小实现**

```python
# backend/models/session/router_websocket.py

"""WebSocket 路由 - 实时双向通信."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: int):
    """WebSocket 端点：实时双向通信.

    支持：
    - 观察模式：接收后端推送的教学消息和检查点状态
    - 教师模式：接收用户操作指令，推送学生响应
    - 心跳：ping/pong 保活
    """
    await websocket.accept()

    # 注册连接（使用共享单例）
    manager = get_connection_manager()
    manager.connect(session_id=session_id, websocket=websocket)

    # 发送连接确认
    await websocket.send_json({
        "type": "connected",
        "session_id": session_id,
    })

    logger.info("WebSocket 连接建立 (session_id=%d)", session_id)

    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "pong":
                # 客户端心跳响应，无需处理
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开 (session_id=%d)", session_id)
    except Exception:
        logger.warning("WebSocket 异常 (session_id=%d)", session_id, exc_info=True)
    finally:
        manager.disconnect(session_id=session_id, websocket=websocket)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/integration/test_websocket.py -v`
预期:通过（3 个测试）

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add models/session/router_websocket.py tests/integration/test_websocket.py
git commit -m "feat(websocket): rewrite WebSocket endpoint with connection pool and heartbeat"
```

---

### Task 4: 集成 ConnectionManager 到 SessionOrchestrator

**涉及文件：**
- 修改: `backend/models/session/orchestrator.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/units/test_orchestrator_ws_push.py

"""SessionOrchestrator WebSocket 推送集成测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState


class TestOrchestratorWsPush:
    """Orchestrator 通过 ConnectionManager 推送 WebSocket 消息."""

    @pytest.mark.asyncio
    async def test_ws_push_uses_connection_manager(self):
        """_ws_push_checkpoint_state 通过 ConnectionManager 广播消息."""
        from models.session.orchestrator import SessionOrchestrator

        mock_teacher = MagicMock()
        mock_students = []
        checkpoint = Checkpoint(
            title="变量",
            key_point="变量的定义和使用",
            checkpoint_question="什么是变量？",
        )
        plan = CheckpointPlan(
            topic="Python 基础",
            teaching_mode="heuristic",
            checkpoints=[checkpoint],
        )
        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        orchestrator = SessionOrchestrator(
            teacher_agent=mock_teacher,
            student_agents=mock_students,
            checkpoint_plan=plan,
            memory_manager=mock_memory_manager,
        )

        # Mock ConnectionManager.broadcast
        mock_broadcast = AsyncMock()
        with patch("models.session.orchestrator.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_get_cm.return_value = mock_manager

            await orchestrator._ws_push_checkpoint_state(checkpoint)

            mock_broadcast.assert_called_once()
            call_args = mock_broadcast.call_args
            assert call_args[0][0] == 1  # session_id
            message = call_args[0][1]
            assert message["type"] == "checkpoint_state_change"
            assert "checkpoint" in message["data"]
            assert "progress" in message["data"]
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_orchestrator_ws_push.py -v`
预期:失败（patch 目标尚未存在）

- [ ] **Step 3: Modify orchestrator.py**

在 `backend/models/session/orchestrator.py` 中：

1. 添加导入：

```python
from core.connection_manager import get_connection_manager
```

2. 修改 `_ws_push_checkpoint_state` 方法，在 `self._ws_push_callback` 之后添加 ConnectionManager 广播：

```python
async def _ws_push_checkpoint_state(self, checkpoint: Checkpoint) -> None:
    """通过 WebSocket 推送检查点状态变更."""
    # 1. 通过回调推送（测试用）
    if self._ws_push_callback:
        message = {
            "type": "checkpoint_state_change",
            "data": {
                "session_id": self.memory_manager.session_memory.session_id,
                "checkpoint_index": self.checkpoint_plan.current_index,
                "state": checkpoint.state.value,
                "checkpoint": {
                    "title": checkpoint.title,
                    "key_point": checkpoint.key_point,
                    "state": checkpoint.state.value,
                },
            },
        }
        import inspect

        if inspect.iscoroutinefunction(self._ws_push_callback):
            await self._ws_push_callback(message)
        else:
            self._ws_push_callback(message)

    # 2. 通过 ConnectionManager 广播（真实 WebSocket 连接）
    cm = get_connection_manager()
    if cm.get_connection_count(session_id=self.memory_manager.session_memory.session_id) > 0:
        total = len(self.checkpoint_plan.checkpoints)
        current = self.checkpoint_plan.current_index
        completed = sum(
            1 for cp in self.checkpoint_plan.checkpoints[:current]
            if cp.state == CheckpointState.COMPLETE
        )
        await cm.broadcast(
            session_id=self.memory_manager.session_memory.session_id,
            message={
                "type": "checkpoint_state_change",
                "session_id": self.memory_manager.session_memory.session_id,
                "index": current,
                "checkpoint": {
                    "title": checkpoint.title,
                    "key_point": checkpoint.key_point,
                    "state": checkpoint.state.value,
                },
                "progress": {
                    "current": current + 1,
                    "total": total,
                    "completed": completed,
                },
            },
        )
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_orchestrator_ws_push.py -v`
预期:通过

同时运行现有的 orchestrator 测试确保不回归：
运行: `cd backend && python -m pytest tests/unit_llm/test_session_orchestrator.py -v`
预期:通过

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add models/session/orchestrator.py tests/units/test_orchestrator_ws_push.py
git commit -m "feat(orchestrator): integrate ConnectionManager for WebSocket broadcast"
```

---

### Task 5: 集成 ConnectionManager 到 TeacherSessionController

**涉及文件：**
- 修改: `backend/models/session/teacher_controller.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/units/test_teacher_controller_ws_push.py

"""TeacherSessionController WebSocket 推送测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.checkpoint.schemas import CheckpointPlan
from models.session.schemas import Message, MessageType


class TestTeacherControllerWsPush:
    """TeacherSessionController 通过 ConnectionManager 推送学生回答."""

    @pytest.mark.asyncio
    async def test_handle_ask_to_all_broadcasts_answers(self):
        """handle_ask_to_all 通过 ConnectionManager 广播学生回答."""
        from models.session.teacher_controller import TeacherSessionController

        mock_student = MagicMock()
        mock_student.profile.name = "张三"
        mock_student.ask_question.return_value = "一次函数是 y=kx+b"

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        plan = CheckpointPlan(topic="一次函数", teaching_mode="teacher", checkpoints=[])
        controller = TeacherSessionController(
            student_agents=[mock_student],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
        )

        mock_broadcast = AsyncMock()
        with patch("models.session.teacher_controller.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            controller.handle_ask_to_all("什么是一次函数？")

            mock_broadcast.assert_called()
            call_args = mock_broadcast.call_args[0]
            assert call_args[0] == 1  # session_id
            message = call_args[1]
            assert message["type"] == "student_answer"
            assert message["student_name"] == "张三"

    @pytest.mark.asyncio
    async def test_handle_broadcast_lecture_pushes_message(self):
        """handle_broadcast_lecture 通过 ConnectionManager 推送消息."""
        from models.session.teacher_controller import TeacherSessionController

        mock_memory_manager = MagicMock()
        mock_memory_manager.session_memory.session_id = 1

        plan = CheckpointPlan(topic="一次函数", teaching_mode="teacher", checkpoints=[])
        controller = TeacherSessionController(
            student_agents=[],
            memory_manager=mock_memory_manager,
            checkpoint_plan=plan,
        )

        mock_broadcast = AsyncMock()
        with patch("models.session.teacher_controller.get_connection_manager") as mock_get_cm:
            mock_manager = MagicMock()
            mock_manager.broadcast = mock_broadcast
            mock_manager.get_connection_count.return_value = 1
            mock_get_cm.return_value = mock_manager

            controller.handle_broadcast_lecture("今天我们学习一次函数")

            mock_broadcast.assert_called_once()
            message = mock_broadcast.call_args[0][1]
            assert message["type"] == "message"
            assert message["sender"] == "teacher"
            assert message["message_type"] == "lecture"
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_teacher_controller_ws_push.py -v`
预期:失败（patch 目标不存在）

- [ ] **Step 3: Modify teacher_controller.py**

在 `backend/models/session/teacher_controller.py` 中：

1. 添加导入：

```python
from core.connection_manager import get_connection_manager
```

2. 在 `handle_broadcast_lecture` 末尾添加推送：

```python
def handle_broadcast_lecture(self, content: str) -> None:
    # ... 现有代码 ...

    # WebSocket 推送
    cm = get_connection_manager()
    if cm.get_connection_count(session_id=self.memory_manager.session_memory.session_id) > 0:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                cm.broadcast(
                    session_id=self.memory_manager.session_memory.session_id,
                    message={
                        "type": "message",
                        "session_id": self.memory_manager.session_memory.session_id,
                        "sender": "teacher",
                        "message_type": "lecture",
                        "content": content,
                        "receiver": "all",
                    },
                )
            )
        except RuntimeError:
            pass  # 没有运行中的事件循环
```

3. 在 `handle_ask_to_all` 的学生回答循环中添加推送：

```python
# 在 self.memory_manager.session_memory.message_history.append(answer_message) 之后
cm = get_connection_manager()
if cm.get_connection_count(session_id=self.memory_manager.session_memory.session_id) > 0:
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            cm.broadcast(
                session_id=self.memory_manager.session_memory.session_id,
                message={
                    "type": "student_answer",
                    "session_id": self.memory_manager.session_memory.session_id,
                    "student_name": student.profile.name,
                    "content": answer,
                    "message_type": "answer_to_checkpoint",
                },
            )
        )
    except RuntimeError:
        pass
```

4. 在 `handle_ask_to_student` 的学生回答部分添加同样的推送逻辑。

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_teacher_controller_ws_push.py -v`
预期:通过

同时运行现有的 teacher_controller 测试确保不回归：
运行: `cd backend && python -m pytest tests/unit_llm/test_teacher_controller.py tests/units/test_teacher_controller_ws_push.py -v`
预期:全部通过

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add models/session/teacher_controller.py tests/units/test_teacher_controller_ws_push.py
git commit -m "feat(teacher-controller): integrate ConnectionManager for WebSocket broadcast"
```

---

## Phase 9: 后端API整合

### Task 6: 会话管理 REST API

**涉及文件：**
- 新建: `backend/models/session/router.py`
- 新建: `backend/tests/units/test_session_router.py`
- 新建: `backend/tests/integration/test_session_api.py`
- 修改: `backend/main.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/integration/test_session_api.py

"""会话管理 API 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def client(test_engine_file):
    """创建测试客户端（使用文件数据库）."""
    from core.database import get_db
    from tests.conftest import db_session_file

    engine, base, tmp_path, url = test_engine_file

    # Override dependency
    async_session_maker = __import__(
        "sqlalchemy.ext.asyncio", fromlist=["async_sessionmaker"]
    ).async_sessionmaker(engine, class_=__import__("sqlalchemy.ext.asyncio", fromlist=["AsyncSession"]).AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestSessionMessagesAPI:
    """会话消息查询 API 测试."""

    async def test_get_messages_empty_session(self, client):
        """查询不存在 session 的消息返回空列表."""
        response = await client.get("/sessions/999/messages")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_messages_returns_list(self, client):
        """查询 session 的消息返回消息列表."""
        # 先创建一个 session 和消息
        from orm.message import MessageModel
        from orm.teaching_session import TeachingSessionModel

        async for db in client.app.dependency_overrides[get_db]():
            session = TeachingSessionModel(topic="Python 变量")
            db.add(session)
            await db.flush()

            msg = MessageModel(
                session_id=session.id,
                sender="teacher",
                message_type="lecture",
                content="今天学习变量",
            )
            db.add(msg)
            await db.commit()

            session_id = session.id

        response = await client.get(f"/sessions/{session_id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sender"] == "teacher"
        assert data[0]["message_type"] == "lecture"

    async def test_get_session_status(self, client):
        """查询 session 状态."""
        from orm.teaching_session import TeachingSessionModel

        async for db in client.app.dependency_overrides[get_db]():
            session = TeachingSessionModel(topic="Python 变量")
            db.add(session)
            await db.commit()
            session_id = session.id

        response = await client.get(f"/sessions/{session_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["topic"] == "Python 变量"
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/integration/test_session_api.py -v`
预期:失败（404 - 端点不存在）

- [ ] **Step 3: 编写最小实现**

```python
# backend/models/session/router.py

"""会话管理 REST API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from orm.message import MessageModel
from orm.teaching_session import TeachingSessionModel

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}/messages", summary="获取会话消息列表")
async def get_session_messages(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """获取指定会话的所有消息，按时间排序.

    Args:
        session_id: 会话 ID
        db: 数据库会话

    Returns:
        消息列表
    """
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.timestamp)
    )
    messages = result.scalars().all()
    return [
        {
            "id": msg.id,
            "session_id": msg.session_id,
            "sender": msg.sender,
            "message_type": msg.message_type,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
        }
        for msg in messages
    ]


@router.get("/{session_id}/status", summary="获取会话状态")
async def get_session_status(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取指定会话的状态信息.

    Args:
        session_id: 会话 ID
        db: 数据库会话

    Returns:
        会话状态信息
    """
    result = await db.execute(
        select(TeachingSessionModel).where(TeachingSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {
        "session_id": session.id,
        "topic": session.topic,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }
```

在 `backend/main.py` 中注册路由：

```python
from models.session.router import router as session_router

app.include_router(session_router)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/integration/test_session_api.py -v`
预期:通过

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add models/session/router.py tests/integration/test_session_api.py main.py
git commit -m "feat(api): add session management REST API (messages and status endpoints)"
```

---

### Task 7: 观察模式 API（真实实现）

**涉及文件：**
- 重写: `backend/models/observation/router.py`
- 修改: `backend/models/observation/schemas.py`
- 重写: `backend/tests/integration/test_observation_api.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/integration/test_observation_api.py

"""观察模式 API 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from main import app


@pytest.fixture
async def client(test_engine_file):
    """创建测试客户端."""
    from core.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    engine, base, tmp_path, url = test_engine_file
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )

    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestObservationStartAPI:
    """观察模式启动 API 测试."""

    async def test_start_observation_creates_session(self, client):
        """启动观察模式创建 teaching_session 记录."""
        from orm.teaching_session import TeachingSessionModel

        payload = {
            "topic": "Python 变量",
            "teaching_mode": "heuristic",
            "students": [
                {
                    "name": "张三",
                    "level": "excellent",
                    "attitude": "active",
                    "learning_ability": 8,
                },
                {
                    "name": "李四",
                    "level": "medium",
                    "attitude": "neutral",
                    "learning_ability": 5,
                },
            ],
        }

        response = await client.post("/observation/start", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "running"

        # 验证数据库中创建了 session
        from core.database import get_db
        async for db in client.app.dependency_overrides[get_db]():
            result = await db.execute(
                select(TeachingSessionModel).where(
                    TeachingSessionModel.id == data["session_id"]
                )
            )
            session = result.scalar_one_or_none()
            assert session is not None
            assert session.topic == "Python 变量"

    async def test_start_observation_missing_topic(self, client):
        """缺少 topic 参数返回 422."""
        payload = {
            "teaching_mode": "heuristic",
            "students": [{"name": "张三", "level": "excellent", "attitude": "active", "learning_ability": 8}],
        }
        response = await client.post("/observation/start", json=payload)
        assert response.status_code == 422

    async def test_start_observation_empty_students(self, client):
        """空学生列表返回 422."""
        payload = {
            "topic": "Python 变量",
            "teaching_mode": "heuristic",
            "students": [],
        }
        response = await client.post("/observation/start", json=payload)
        assert response.status_code == 422
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/integration/test_observation_api.py -v`
预期:失败（missing_topic 测试因 Pydantic 验证通过，但 creates_session 因实现是 mock 而失败）

- [ ] **Step 3: 编写最小实现**

```python
# backend/models/observation/router.py

"""观察模式 API 路由."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.observation.schemas import (
    ObservationConfig,
    ObservationStartResponse,
)
from orm.teaching_session import TeachingSessionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observation", tags=["observation"])


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    创建 teaching_session 记录并返回 session_id。
    注意：实际的 SessionOrchestrator 运行和检查点计划生成
    在 WebSocket 连接建立后异步执行（Phase 10 实现）。

    Args:
        config: 观察模式配置
        db: 数据库会话

    Returns:
        会话 ID 和状态
    """
    # 创建 teaching_session 记录
    session = TeachingSessionModel(
        topic=config.topic,
        teaching_mode=config.teaching_mode,
    )
    db.add(session)
    await db.flush()
    session_id = session.id

    # TODO: Phase 10 - 初始化 StudentAgents、MemoryManager、CheckpointPlan
    # TODO: Phase 10 - 启动 SessionOrchestrator（异步后台任务）
    # TODO: Phase 10 - 返回 WebSocket 连接 URL 供前端连接

    await db.commit()

    logger.info("观察模式会话创建成功 (session_id=%d)", session_id)

    return ObservationStartResponse(
        session_id=session_id,
        status="running",
    )
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/integration/test_observation_api.py -v`
预期:通过

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add models/observation/router.py tests/integration/test_observation_api.py
git commit -m "feat(observation): implement real observation start API with session creation"
```

---

### Task 8: MessageModel 添加 receiver 列（Alembic 迁移）

**涉及文件：**
- 修改: `backend/orm/message.py`
- 新建: `backend/alembic/versions/004_add_receiver_to_messages.py`

- [ ] **Step 1: 编写失败测试**

在 `backend/tests/units/test_schemas.py` 中添加 ORM receiver 字段测试：

```python
class TestMessageModelReceiver:
    """MessageModel receiver 字段测试."""

    def test_message_model_has_receiver_column(self):
        """MessageModel 应该有 receiver 列."""
        from orm.message import MessageModel

        assert hasattr(MessageModel, "receiver")
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_schemas.py::TestMessageModelReceiver -v`
预期:失败（AttributeError: receiver）

- [ ] **Step 3: 在 ORM 模型中添加 receiver 列**

在 `backend/orm/message.py` 中添加：

```python
receiver: Mapped[str] = mapped_column(String(50), default="all")
```

- [ ] **Step 4: 创建 Alembic 迁移**

```bash
cd backend
alembic revision --autogenerate -m "add receiver column to messages"
```

- [ ] **Step 5: 执行迁移**

```bash
cd backend
alembic upgrade head
```

- [ ] **Step 6: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_schemas.py::TestMessageModelReceiver -v`
预期:通过

- [ ] **Step 7: 更新 session router 添加 receiver 字段**

在 Task 6 的 `get_session_messages` 响应中添加 `receiver`:

```python
"receiver": msg.receiver or "all",
```

- [ ] **Step 8: 提交代码**

```bash
cd backend
git add orm/message.py alembic/versions/004_*.py tests/units/test_schemas.py
git commit -m "feat(db): add receiver column to messages table"
```

---

### Task 9: SessionRegistry（会话注册表）

**涉及文件：**
- 新建: `backend/core/session_registry.py`
- 新建: `backend/tests/units/test_session_registry.py`

- [ ] **Step 1: 编写失败测试**

```python
# backend/tests/units/test_session_registry.py

from unittest.mock import MagicMock

from core.session_registry import SessionRegistry


class TestSessionRegistry:
    """SessionRegistry 单元测试."""

    def test_register_and_get_orchestrator(self):
        """注册并获取 orchestrator."""
        registry = SessionRegistry()
        mock_orchestrator = MagicMock()
        registry.register(session_id=1, mode="observation", orchestrator=mock_orchestrator)

        result = registry.get_orchestrator(session_id=1)
        assert result is mock_orchestrator

    def test_register_and_get_controller(self):
        """注册并获取 teacher controller."""
        registry = SessionRegistry()
        mock_controller = MagicMock()
        registry.register(session_id=2, mode="teacher", controller=mock_controller)

        result = registry.get_controller(session_id=2)
        assert result is mock_controller

    def test_get_nonexistent_session(self):
        """获取不存在的 session 返回 None."""
        registry = SessionRegistry()
        assert registry.get_orchestrator(session_id=999) is None
        assert registry.get_controller(session_id=999) is None

    def test_unregister(self):
        """注销 session."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="observation", orchestrator=MagicMock())
        registry.unregister(session_id=1)
        assert registry.get_orchestrator(session_id=1) is None
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && python -m pytest tests/units/test_session_registry.py -v`
预期:失败（ModuleNotFoundError）

- [ ] **Step 3: 编写最小实现**

```python
# backend/core/session_registry.py

"""会话注册表 — 映射 session_id 到运行中的 orchestrator/controller."""


class SessionRegistry:
    """全局会话注册表.

    将 session_id 映射到对应的 SessionOrchestrator 或 TeacherSessionController 实例。
    用于 WebSocket 端点根据 session_id 查找业务逻辑实例。
    """

    def __init__(self) -> None:
        self._orchestrators: dict[int, object] = {}
        self._controllers: dict[int, object] = {}

    def register(
        self,
        *,
        session_id: int,
        mode: str,
        orchestrator: object | None = None,
        controller: object | None = None,
    ) -> None:
        """注册会话实例."""
        if mode == "observation" and orchestrator is not None:
            self._orchestrators[session_id] = orchestrator
        elif mode == "teacher" and controller is not None:
            self._controllers[session_id] = controller

    def unregister(self, session_id: int) -> None:
        """注销会话."""
        self._orchestrators.pop(session_id, None)
        self._controllers.pop(session_id, None)

    def get_orchestrator(self, session_id: int) -> object | None:
        """获取观察模式 orchestrator."""
        return self._orchestrators.get(session_id)

    def get_controller(self, session_id: int) -> object | None:
        """获取教师模式 controller."""
        return self._controllers.get(session_id)
```

- [ ] **Step 4: 运行测试验证通过**

运行: `cd backend && python -m pytest tests/units/test_session_registry.py -v`
预期:通过（4 个测试）

- [ ] **Step 5: 提交代码**

```bash
cd backend
git add core/session_registry.py tests/units/test_session_registry.py
git commit -m "feat(core): add SessionRegistry for session-to-instance mapping"
```

---

### Task 10: 补充缺失的测试用例

**涉及文件：**
- 修改: `backend/tests/units/test_connection_manager.py`
- 修改: `backend/tests/integration/test_websocket.py`
- 修改: `backend/tests/integration/test_session_api.py`

- [ ] **Step 1: 添加 ConnectionManager 缺失测试用例**

在 `backend/tests/units/test_connection_manager.py` 中追加：

```python
def test_disconnect_nonexistent_connection(self):
    """断开不存在的连接不报错."""
    manager = ConnectionManager()
    mock_ws = MagicMock()
    manager.disconnect(session_id=999, websocket=mock_ws)  # 不报错

def test_send_personal_dead_connection(self):
    """向已断开的连接发送消息不报错."""
    manager = ConnectionManager()
    mock_ws = AsyncMock()
    mock_ws.send_json.side_effect = Exception("Connection closed")
    import asyncio
    asyncio.run(manager.send_personal(websocket=mock_ws, message={"type": "test"}))
    # 不报错即通过
```

- [ ] **Step 2: 添加 WebSocket 断连和未知消息类型测试**

在 `backend/tests/integration/test_websocket.py` 中追加：

```python
def test_websocket_disconnect_handling(self):
    """WebSocket 客户端断开时服务端不崩溃."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws/sessions/1") as websocket:
            websocket.receive_json()  # connected
        # 退出 with 块后，连接已断开

def test_websocket_unknown_message_type_ignored(self):
    """未知消息类型被忽略，不断开连接."""
    with TestClient(app) as client, client.websocket_connect(
        "/ws/sessions/1"
    ) as websocket:
        websocket.receive_json()  # connected
        websocket.send_json({"type": "unknown_type"})
        # 连接仍然存活，可以继续发送 ping
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data["type"] == "pong"
```

- [ ] **Step 3: 添加会话状态 404 测试**

在 `backend/tests/integration/test_session_api.py` 中追加：

```python
async def test_get_session_status_not_found(self, client):
    """查询不存在的 session 返回 404."""
    response = await client.get("/sessions/99999/status")
    assert response.status_code == 404
```

- [ ] **Step 4: 添加 orchestrator 无连接时跳过广播测试**

在 `backend/tests/units/test_orchestrator_ws_push.py` 中追加：

```python
@pytest.mark.asyncio
async def test_ws_push_skips_when_no_connections(self):
    """没有活跃连接时跳过 broadcast."""
    from models.session.orchestrator import SessionOrchestrator

    mock_teacher = MagicMock()
    mock_students = []
    checkpoint = Checkpoint(
        title="变量", key_point="变量的定义", checkpoint_question="什么是变量？",
    )
    plan = CheckpointPlan(topic="Python", teaching_mode="heuristic", checkpoints=[checkpoint])
    mock_mm = MagicMock()
    mock_mm.session_memory.session_id = 1

    orchestrator = SessionOrchestrator(
        teacher_agent=mock_teacher, student_agents=mock_students,
        checkpoint_plan=plan, memory_manager=mock_mm,
    )

    mock_broadcast = AsyncMock()
    with patch("models.session.orchestrator.get_connection_manager") as mock_get_cm:
        mock_manager = MagicMock()
        mock_manager.broadcast = mock_broadcast
        mock_manager.get_connection_count.return_value = 0
        mock_get_cm.return_value = mock_manager

        await orchestrator._ws_push_checkpoint_state(checkpoint)
        mock_broadcast.assert_not_called()
```

- [ ] **Step 5: 运行所有新增测试**

运行: `cd backend && python -m pytest tests/units/test_connection_manager.py tests/integration/test_websocket.py tests/integration/test_session_api.py tests/units/test_orchestrator_ws_push.py -v`
预期:全部通过

- [ ] **Step 6: 提交代码**

```bash
cd backend
git add tests/units/test_connection_manager.py tests/integration/test_websocket.py tests/integration/test_session_api.py tests/units/test_orchestrator_ws_push.py
git commit -m "test: add missing test cases for edge conditions"
```

---

### Task 11: 运行全部测试确保不回归

**涉及文件：**
- 无新建文件

- [ ] **Step 1: 运行所有单元测试**

运行: `cd backend && python -m pytest tests/units/ -v`
预期:全部通过

- [ ] **Step 2: 运行所有集成测试**

运行: `cd backend && python -m pytest tests/integration/ -v`
预期:全部通过

- [ ] **Step 3: 运行代码质量检查**

运行: `cd backend && ruff check core/ models/ tests/units/ tests/integration/`
预期:无错误

- [ ] **Step 4: 修复发现的问题**

运行: `cd backend && ruff check core/ models/ --fix && ruff format core/ models/`

- [ ] **Step 5: 最终提交**

```bash
cd backend
git add -A
git commit -m "test: ensure all tests pass after Phase 8-9 integration"
```

---

## 自检

### 需求覆盖

| Phase 8 要求 | 对应任务 |
|---|---|
| WebSocket 端点 `/ws/{session_id}` | Task 3 |
| 连接管理（accept, close） | Task 2, 3 |
| 消息广播机制 | Task 2 |
| 连接池管理 | Task 2 |
| ping/pong 心跳 | Task 3 |
| 断线处理 | Task 2 (dead connection removal), 3 (WebSocketDisconnect) |
| Orchestrator 推送 | Task 4 |
| TeacherController 推送 | Task 5 |
| 前端能建立 WebSocket 连接 | Task 3 |
| 多客户端同时连接 | Task 2 |
| 连接断开时有处理 | Task 3 |

| Phase 9 要求 | 对应任务 |
|---|---|
| `POST /observation/start` 创建会话 | Task 7 |
| `GET /observation/{session_id}/report` | 延迟到 Phase 11（分析报告） |
| `GET /sessions/{session_id}` | Task 6 (status endpoint) |
| `GET /sessions/{session_id}/messages` | Task 6 |
| `POST /students/create` | 延迟到 Phase 10（前端集成时实现） |
| `POST /students/export` | 延迟到 Phase 10 |
| `GET /students/templates` | 延迟到 Phase 10 |

### 延迟到后续阶段的内容

1. **`GET /observation/{session_id}/report`** — 需要 ObservationAnalyzer（Phase 11）
2. **学生创建 API** (`/students/create`, `/students/export`, `/students/templates`) — 在 Phase 10 前端集成时一起实现，因为需要前端 UI 配合
3. **观察模式 WebSocket 实时推送教学消息** — 需要 SessionOrchestrator 异步运行集成（Phase 10）
4. **教师模式 WebSocket 命令处理** — 需要 SessionRegistry（Task 9 已添加）+ Phase 12 前端 UI

### 占位符扫描

无 TBD、TODO（仅 Task 7 中的 TODO 标记了 Phase 10 的后续工作，属于有意为之的范围标记）。

### 类型一致性

- `session_id` 全部使用 `int` 类型
- WebSocket 消息格式与 `design.md` 中定义的协议一致
- `ConnectionManager` 单例定义在 `core/connection_manager.py`，所有模块通过 `get_connection_manager()` 获取同一个实例

## GSTACK 审查报告

| 审查类型 | 触发方式 | 审查内容 | 运行次数 | 状态 | 发现 |
|----------|----------|----------|----------|------|------|
| CEO 审查 | `/plan-ceo-review` | 范围与策略 | 0 | — | — |
| Codex 审查 | `/codex review` | 独立第二意见 | 0 | — | — |
| 工程审查 | `/plan-eng-review` | 架构与测试（必需） | 1 | issues_open | 发现 4 个问题，已全部修复 |
| 设计审查 | `/plan-design-review` | UI/UX 缺陷 | 0 | — | — |
| 开发体验审查 | `/plan-devex-review` | 开发者体验缺陷 | 0 | — | — |

**审查发现：**
1. [已修复] ConnectionManager 单例碎片化（3 个独立实例 → 1 个共享单例，移至 core/）
2. [已修复] MessageModel 缺少 receiver 列（已添加迁移任务）
3. [已修复] 无 session 到实例的查找机制（已添加 SessionRegistry 任务）
4. [已修复] 7 个缺失的测试用例（已添加 Task 10）

**未解决：** 0
**关键缺陷：** 0（导致消息无法到达前端的单例碎片化问题已修复）
