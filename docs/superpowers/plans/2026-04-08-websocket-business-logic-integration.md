# WebSocket 与业务逻辑集成 实施计划

> **For agentic workers（智能体工作者）:** 必须使用 `superpowers:test-driven-development` 技能逐步执行此计划。每个任务遵循 RED-GREEN-REFACTOR-COMMIT 循环。步骤使用复选框 (`- [ ]`) 语法追踪进度。

**目标:** 将 WebSocket 端点从单向广播通道升级为双向通信通道，使其能接收前端命令并路由到 SessionOrchestrator（观察模式）或 TeacherSessionController（教师模式），实现 WebSocket 与大模型的端到端集成。

**架构:** WebSocket 端点接收 JSON 命令，通过 SessionRegistry 查找对应的业务逻辑实例（orchestrator 或 controller），调用对应方法，结果通过 ConnectionManager 推送回客户端。观察模式通过 `POST /observation/start` 初始化 orchestrator 并注册到 SessionRegistry，然后后台异步运行。教师模式通过 WebSocket 命令逐步驱动教学流程。

**技术栈:** FastAPI WebSocket, asyncio, SessionRegistry, ConnectionManager, LLMClient, httpx (测试)

---

## 文件结构

```
backend/
├── models/
│   └── session/
│       ├── router_websocket.py    # [重写] 添加命令路由到 orchestrator/controller
│       └── schemas.py             # [修改] 添加 WebSocket 命令 schemas
├── models/
│   └── observation/
│       └── router.py              # [重写] 初始化 orchestrator 并注册到 SessionRegistry，后台运行
├── core/
│   └── session_registry.py        # [修改] 添加类型标注，接入 WebSocket 端点
├── tests/
│   ├── units/
│   │   ├── test_ws_command_router.py      # [新建] WebSocket 命令路由单元测试
│   │   └── test_session_registry.py       # [修改] 更新类型标注后的测试
│   └── integration/
│       ├── test_websocket.py             # [重写] 添加命令路由集成测试
│       └── test_observation_api.py       # [重写] 验证 orchestrator 初始化和后台运行
└── docs/
    ├── api.md                          # [修改] 添加 WebSocket 命令文档
    └── tests/backend/index.md           # [修改] 更新测试文档
```

---

## Task 1: WebSocket 命令 Schemas

**涉及文件：**
- 修改: `backend/models/session/schemas.py`

- [ ] **Step 1: 编写失败测试**

在 `backend/tests/units/test_ws_command_router.py` 中添加 WebSocket 命令 schema 测试：

```python
# backend/tests/units/test_ws_command_router.py

"""WebSocket 命令 schema 测试."""

from pydantic import ValidationError

import pytest


class TestWsCommandSchemas:
    """WebSocket 命令 schema 验证测试."""

    def test_broadcast_lecture_command_valid(self):
        """合法的 broadcast_lecture 命令."""
        from models.session.schemas import WsBroadcastLectureCommand

        cmd = WsBroadcastLectureCommand(content="今天我们学习 Python 变量")
        assert cmd.type == "broadcast_lecture"
        assert cmd.content == "今天我们学习 Python 变量"

    def test_broadcast_lecture_command_missing_content(self):
        """缺少 content 字段应报错."""
        from models.session.schemas import WsBroadcastLectureCommand

        with pytest.raises(ValidationError):
            WsBroadcastLectureCommand(type="broadcast_lecture")

    def test_ask_to_all_command_valid(self):
        """合法的 ask_to_all 命令."""
        from models.session.schemas import WsAskToAllCommand

        cmd = WsAskToAllCommand(question="什么是变量？")
        assert cmd.type == "ask_to_all"
        assert cmd.question == "什么是变量？"

    def test_ask_to_all_command_missing_question(self):
        """缺少 question 字段应报错."""
        from models.session.schemas import WsAskToAllCommand

        with pytest.raises(ValidationError):
            WsAskToAllCommand(type="ask_to_all")

    def test_ask_to_student_command_valid(self):
        """合法的 ask_to_student 命令."""
        from models.session.schemas import WsAskToStudentCommand

        cmd = WsAskToStudentCommand(question="什么是变量？", student_name="张三")
        assert cmd.type == "ask_to_student"
        assert cmd.student_name == "张三"

    def test_ask_to_student_command_missing_fields(self):
        """缺少 student_name 字段应报错."""
        from models.session.schemas import WsAskToStudentCommand

        with pytest.raises(ValidationError):
            WsAskToStudentCommand(type="ask_to_student", question="测试")

    def test_teacher_reply_command_valid(self):
        """合法的 teacher_reply 命令."""
        from models.session.schemas import WsTeacherReplyCommand

        cmd = WsTeacherReplyCommand(reply="回答正确", student_name="张三")
        assert cmd.type == "teacher_reply"
        assert cmd.student_name == "张三"

    def test_advance_checkpoint_command_valid(self):
        """合法的 advance_checkpoint 命令."""
        from models.session.schemas import WsAdvanceCheckpointCommand

        cmd = WsAdvanceCheckpointCommand()
        assert cmd.type == "advance_checkpoint"

    def test_end_dialogue_command_valid(self):
        """合法的 end_dialogue 命令."""
        from models.session.schemas import WsEndDialogueCommand

        cmd = WsEndDialogueCommand()
        assert cmd.type == "end_dialogue"

    def test_assign_homework_command_valid(self):
        """合法的 assign_homework 命令."""
        from models.session.schemas import WsAssignHomeworkCommand

        cmd = WsAssignHomeworkCommand(content="完成课后作业")
        assert cmd.type == "assign_homework"
        assert cmd.content == "完成课后作业"

    def test_collect_homework_command_valid(self):
        """合法的 collect_homework 命令."""
        from models.session.schemas import WsCollectHomeworkCommand

        cmd = WsCollectHomeworkCommand(homework_prompt="完成练习1和练习2")
        assert cmd.type == "collect_homework"

    def test_end_teaching_command_valid(self):
        """合法的 end_teaching 命令."""
        from models.session.schemas import WsEndTeachingCommand

        cmd = WsEndTeachingCommand()
        assert cmd.type == "end_teaching"

    def test_unknown_command_type_rejected(self):
        """未知命令类型应报错."""
        from models.session.schemas import WsTeacherCommand

        with pytest.raises(ValidationError):
            WsTeacherCommand(type="unknown_command")
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/units/test_ws_command_router.py -v`
Expected: FAIL — ImportError: cannot import `WsBroadcastLectureCommand` etc.

- [ ] **Step 3: 实现 schemas**

在 `backend/models/session/schemas.py` 末尾添加：

```python
class WsBroadcastLectureCommand(BaseModel):
    """WebSocket 命令: 广播讲授."""

    type: str = "broadcast_lecture"
    content: str = Field(min_length=1, description="讲授内容")


class WsAskToAllCommand(BaseModel):
    """WebSocket 命令: 向全体提问."""

    type: str = "ask_to_all"
    question: str = Field(min_length=1, description="问题内容")


class WsAskToStudentCommand(BaseModel):
    """WebSocket 命令: 向指定学生提问."""

    type: str = "ask_to_student"
    question: str = Field(min_length=1, description="问题内容")
    student_name: str = Field(min_length=1, description="目标学生名称")


class WsTeacherReplyCommand(BaseModel):
    """WebSocket 命令: 教师回复学生."""

    type: str = "teacher_reply"
    reply: str = Field(min_length=1, description="回复内容")
    student_name: str = Field(min_length=1, description="目标学生名称")


class WsAdvanceCheckpointCommand(BaseModel):
    """WebSocket 命令: 推进到下一个检查点."""

    type: str = "advance_checkpoint"


class WsEndDialogueCommand(BaseModel):
    """WebSocket 命令: 结束当前对话."""

    type: str = "end_dialogue"


class WsAssignHomeworkCommand(BaseModel):
    """WebSocket 命令: 布置作业."""

    type: str = "assign_homework"
    content: str = Field(min_length=1, description="作业内容")


class WsCollectHomeworkCommand(BaseModel):
    """WebSocket 命令: 收集作业."""

    type: str = "collect_homework"
    homework_prompt: str = Field(min_length=1, description="作业要求")


class WsEndTeachingCommand(BaseModel):
    """WebSocket 命令: 结束教学."""

    type: str = "end_teaching"


class WsTeacherCommand(BaseModel):
    """教师模式 WebSocket 命令（联合类型）.

    type 字段用于路由到对应的 handler。
    """
    type: str = Field(
        description="命令类型",
        pattern="^(broadcast_lecture|ask_to_all|ask_to_student|teacher_reply|advance_checkpoint|end_dialogue|assign_homework|collect_homework|end_teaching)$",
    )
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/units/test_ws_command_router.py -v`
Expected: ALL PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add models/session/schemas.py tests/units/test_ws_command_router.py
git commit -m "feat(ws): add WebSocket command schemas with validation"
```

---

## Task 2: SessionRegistry 类型标注更新

**涉及文件：**
- 修改: `backend/core/session_registry.py`
- 修改: `backend/tests/units/test_session_registry.py`

- [ ] **Step 1: 编写失败测试**

在 `backend/tests/units/test_session_registry.py` 中添加类型标注测试：

```python
class TestSessionRegistryTypes:
    """SessionRegistry 类型标注测试."""

    def test_register_controller_returns_controller(self):
        """注册 controller 后 get_controller 返回正确类型."""
        from models.session.teacher_controller import TeacherSessionController

        mock_controller = MagicMock(spec=TeacherSessionController)
        registry = SessionRegistry()
        registry.register(session_id=1, mode="teacher", controller=mock_controller)

        result = registry.get_controller(session_id=1)
        assert result is mock_controller

    def test_get_orchestrator_none_for_teacher_session(self):
        """教师模式会话的 get_orchestrator 返回 None."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="teacher", controller=MagicMock())

        assert registry.get_orchestrator(session_id=1) is None

    def test_get_controller_none_for_observation_session(self):
        """观察模式会话的 get_controller 返回 None."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="observation", orchestrator=MagicMock())

        assert registry.get_controller(session_id=1) is None

    def test_get_session_info_observation(self):
        """观察模式会话 get_session_info 返回 mode='observation'."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="observation", orchestrator=MagicMock())

        info = registry.get_session_info(session_id=1)
        assert info == {"mode": "observation"}

    def test_get_session_info_teacher(self):
        """教师模式会话 get_session_info 返回 mode='teacher'."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="teacher", controller=MagicMock())

        info = registry.get_session_info(session_id=1)
        assert info == {"mode": "teacher"}

    def test_get_session_info_not_found(self):
        """不存在的会话 get_session_info 返回 None."""
        registry = SessionRegistry()

        assert registry.get_session_info(session_id=999) is None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/units/test_session_registry.py -v`
Expected: FAIL — `AttributeError: 'SessionRegistry' object has no attribute 'get_session_info'`

- [ ] **Step 3: 更新 SessionRegistry**

在 `backend/core/session_registry.py` 中添加类型标注和 `get_session_info` 方法：

```python
from __future__ import annotations

"""会话注册表 — 映射 session_id 到运行中的 orchestrator/controller.

用于 WebSocket 端点根据 session_id 查找业务逻辑实例。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.session.orchestrator import SessionOrchestrator
    from models.session.teacher_controller import TeacherSessionController


class SessionRegistry:
    """全局会话注册表.

    将 session_id 映射到对应的 SessionOrchestrator 或 TeacherSessionController 实例。
    用于 WebSocket 端点根据 session_id 查找业务逻辑实例。
    """

    def __init__(self) -> None:
        self._orchestrators: dict[int, SessionOrchestrator] = {}
        self._controllers: dict[int, TeacherSessionController] = {}
        self._session_modes: dict[int, str] = {}  # session_id -> "observation" | "teacher"

    def register(
        self,
        *,
        session_id: int,
        mode: str,
        orchestrator: SessionOrchestrator | None = None,
        controller: TeacherSessionController | None = None,
    ) -> None:
        """注册会话实例."""
        if mode == "observation" and orchestrator is not None:
            self._orchestrators[session_id] = orchestrator
            self._session_modes[session_id] = "observation"
        elif mode == "teacher" and controller is not None:
            self._controllers[session_id] = controller
            self._session_modes[session_id] = "teacher"

    def unregister(self, session_id: int) -> None:
        """注销会话."""
        self._orchestrators.pop(session_id, None)
        self._controllers.pop(session_id, None)
        self._session_modes.pop(session_id, None)

    def get_orchestrator(self, session_id: int) -> SessionOrchestrator | None:
        """获取观察模式 orchestrator."""
        return self._orchestrators.get(session_id)

    def get_controller(self, session_id: int) -> TeacherSessionController | None:
        """获取教师模式 controller."""
        return self._controllers.get(session_id)

    def get_session_info(self, session_id: int) -> dict[str, str] | None:
        """获取会话模式信息.

        Returns:
            {"mode": "observation"} 或 {"mode": "teacher"}，不存在则返回 None
        """
        mode = self._session_modes.get(session_id)
        if mode is None:
            return None
        return {"mode": mode}
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/units/test_session_registry.py -v`
Expected: ALL PASS (10 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add core/session_registry.py tests/units/test_session_registry.py
git commit -m "refactor(session-registry): add type annotations and get_session_info"
```

---

## Task 3: WebSocket 端点命令路由

**涉及文件：**
- 重写: `backend/models/session/router_websocket.py`
- 新建: `backend/tests/units/test_ws_command_router.py` (已存在，追加)

- [ ] **Step 1: 编写失败测试**

在 `backend/tests/units/test_ws_command_router.py` 追加命令路由测试：

```python
"""WebSocket 命令路由单元测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.session.schemas import (
    WsAskToAllCommand,
    WsBroadcastLectureCommand,
    WsEndTeachingCommand,
)


class TestWsCommandRouter:
    """WebSocket 端点命令路由测试."""

    @pytest.mark.asyncio
    async def test_broadcast_lecture_routes_to_controller(self):
        """broadcast_lecture 命令路由到 TeacherSessionController.handle_broadcast_lecture."""
        mock_controller = MagicMock()
        mock_controller.handle_broadcast_lecture = MagicMock()

        with patch("models.session.router_websocket.get_connection_manager") as mock_cm, \
             patch("models.session.router_websocket.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            # 模拟 WebSocket
            mock_ws = AsyncMock()
            mock_ws.receive_json = AsyncMock(
                return_value={"type": "broadcast_lecture", "content": "测试讲授"}
            )

            from models.session.router_websocket import _handle_command

            await _handle_command(mock_ws, 1, {"type": "broadcast_lecture", "content": "测试讲授"})

            mock_controller.handle_broadcast_lecture.assert_called_once_with("测试讲授")

    @pytest.mark.asyncio
    async def test_ask_to_all_routes_to_controller(self):
        """ask_to_all 命令路由到 TeacherSessionController.handle_ask_to_all."""
        mock_controller = MagicMock()
        mock_controller.handle_ask_to_all = MagicMock()

        with patch("models.session.router_websocket.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.router_websocket import _handle_command

            await _handle_command(
                MagicMock(), 1, {"type": "ask_to_all", "question": "什么是变量？"}
            )

            mock_controller.handle_ask_to_all.assert_called_once_with("什么是变量？")

    @pytest.mark.asyncio
    async def test_unknown_command_returns_error(self):
        """未知命令类型返回 error 响应."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        with patch("models.session.router_websocket.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_sr.return_value = mock_registry

            from models.session.router_websocket import _handle_command

            await _handle_command(mock_ws, 1, {"type": "nonexistent"})

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "error"
            assert "unknown command" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_no_session_returns_error(self):
        """session 不存在时返回 error 响应."""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        with patch("models.session.router_websocket.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = None
            mock_sr.return_value = mock_registry

            from models.session.router_websocket import _handle_command

            await _handle_command(mock_ws, 1, {"type": "broadcast_lecture", "content": "测试"})

            mock_ws.send_json.assert_called_once()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "error"
            assert "not found" in call_args["message"].lower()

    @pytest.mark.asyncio
    async def test_advance_checkpoint_routes_to_controller(self):
        """advance_checkpoint 命令路由到 TeacherSessionController.handle_advance_checkpoint."""
        mock_controller = MagicMock()
        mock_controller.handle_advance_checkpoint = MagicMock()

        with patch("models.session.router_websocket.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.router_websocket import _handle_command

            await _handle_command(mock_ws, 1, {"type": "advance_checkpoint"})

            mock_controller.handle_advance_checkpoint.assert_called_once()

    @pytest.mark.asyncio
    async def test_command_result_pushed_via_websocket(self):
        """命令执行结果通过 WebSocket 推送回客户端."""
        mock_controller = MagicMock()
        mock_controller.handle_broadcast_lecture = MagicMock()

        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        with patch("models.session.router_websocket.get_connection_manager"), \
             patch("models.session.router_websocket.get_session_registry") as mock_sr:
            mock_registry = MagicMock()
            mock_registry.get_session_info.return_value = {"mode": "teacher"}
            mock_registry.get_controller.return_value = mock_controller
            mock_sr.return_value = mock_registry

            from models.session.router_websocket import _handle_command

            await _handle_command(mock_ws, 1, {"type": "broadcast_lecture", "content": "测试"})

            # 验证发送了成功响应
            mock_ws.send_json.assert_called()
            call_args = mock_ws.send_json.call_args[0][0]
            assert call_args["type"] == "command_result"
            assert call_args["command"] == "broadcast_lecture"
            assert call_args["success"] is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/units/test_ws_command_router.py -v`
Expected: FAIL — `ImportError: cannot import name '_handle_command'`

- [ ] **Step 3: 重写 router_websocket.py**

```python
"""WebSocket 路由 - 实时双向通信."""

import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from core.connection_manager import get_connection_manager
from core.session_registry import SessionRegistry
from models.session.schemas import (
    WsAdvanceCheckpointCommand,
    WsAskToAllCommand,
    WsAskToStudentCommand,
    WsAssignHomeworkCommand,
    WsBroadcastLectureCommand,
    WsCollectHomeworkCommand,
    WsEndDialogueCommand,
    WsEndTeachingCommand,
    WsTeacherCommand,
    WsTeacherReplyCommand,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 模块级 SessionRegistry 实例（应用生命周期内唯一）
_session_registry = SessionRegistry()


def get_session_registry() -> SessionRegistry:
    """获取全局 SessionRegistry 实例（用于测试注入）."""
    return _session_registry


def set_session_registry(registry: SessionRegistry) -> None:
    """设置全局 SessionRegistry 实例（用于测试注入）."""
    global _session_registry
    _session_registry = registry


# 教师模式命令映射
_TEACHER_COMMAND_HANDLERS = {
    "broadcast_lecture": "_handle_broadcast_lecture",
    "ask_to_all": "_handle_ask_to_all",
    "ask_to_student": "_handle_ask_to_student",
    "teacher_reply": "_handle_teacher_reply",
    "advance_checkpoint": "_handle_advance_checkpoint",
    "end_dialogue": "_handle_end_dialogue",
    "assign_homework": "_handle_assign_homework",
    "collect_homework": "_handle_collect_homework",
    "end_teaching": "_handle_end_teaching",
}


async def _handle_command(
    websocket: WebSocket, session_id: int, data: dict[str, Any]
) -> None:
    """处理 WebSocket 命令并路由到对应的 handler.

    Args:
        websocket: WebSocket 连接实例
        session_id: 会话 ID
        data: 接收到的 JSON 数据
    """
    registry = get_session_registry()
    session_info = registry.get_session_info(session_id)

    if session_info is None:
        await websocket.send_json({
            "type": "error",
            "message": f"Session {session_id} not found",
            "session_id": session_id,
        })
        return

    mode = session_info["mode"]
    command_type = data.get("type", "")

    if mode == "teacher":
        await _handle_teacher_command(websocket, session_id, command_type, data, registry)
    else:
        # 观察模式：当前 orchestrator 自动运行，WebSocket 只接收观察命令
        await websocket.send_json({
            "type": "error",
            "message": f"Observation mode does not support command '{command_type}'",
            "session_id": session_id,
        })


async def _handle_teacher_command(
    websocket: WebSocket,
    session_id: int,
    command_type: str,
    data: dict[str, Any],
    registry: SessionRegistry,
) -> None:
    """处理教师模式命令."""
    controller = registry.get_controller(session_id)
    if controller is None:
        await websocket.send_json({
            "type": "error",
            "message": f"No controller for session {session_id}",
            "session_id": session_id,
        })
        return

    handler_name = _TEACHER_COMMAND_HANDLERS.get(command_type)
    if handler_name is None:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown command: {command_type}",
            "session_id": session_id,
        })
        return

    try:
        await getattr(_TeacherCommandHandlers, handler_name)(websocket, session_id, data, controller)
    except ValidationError as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Invalid command data: {e}",
            "command": command_type,
            "session_id": session_id,
        })
    except Exception as e:
        logger.error("Command '%s' failed: %s", command_type, e, exc_info=True)
        await websocket.send_json({
            "type": "error",
            "message": f"Command '{command_type}' failed: {e}",
            "command": command_type,
            "session_id": session_id,
        })


class _TeacherCommandHandlers:
    """教师模式命令处理器（静态方法集合）."""

    @staticmethod
    async def _handle_broadcast_lecture(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsBroadcastLectureCommand(**data)
        controller.handle_broadcast_lecture(cmd.content)
        await websocket.send_json({
            "type": "command_result",
            "command": "broadcast_lecture",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_ask_to_all(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsAskToAllCommand(**data)
        controller.handle_ask_to_all(cmd.question)
        await websocket.send_json({
            "type": "command_result",
            "command": "ask_to_all",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_ask_to_student(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsAskToStudentCommand(**data)
        result = controller.handle_ask_to_student(cmd.question, cmd.student_name)
        await websocket.send_json({
            "type": "command_result",
            "command": "ask_to_student",
            "success": True,
            "session_id": session_id,
            "data": result,
        })

    @staticmethod
    async def _handle_teacher_reply(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsTeacherReplyCommand(**data)
        controller.handle_teacher_reply(cmd.reply, cmd.student_name)
        await websocket.send_json({
            "type": "command_result",
            "command": "teacher_reply",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_advance_checkpoint(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        controller.handle_advance_checkpoint()
        await websocket.send_json({
            "type": "command_result",
            "command": "advance_checkpoint",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_end_dialogue(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        controller.handle_end_dialogue()
        await websocket.send_json({
            "type": "command_result",
            "command": "end_dialogue",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_assign_homework(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsAssignHomeworkCommand(**data)
        controller.handle_assign_homework(cmd.content)
        await websocket.send_json({
            "type": "command_result",
            "command": "assign_homework",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_collect_homework(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsCollectHomeworkCommand(**data)
        controller.handle_collect_homework(cmd.homework_prompt)
        await websocket.send_json({
            "type": "command_result",
            "command": "collect_homework",
            "success": True,
            "session_id": session_id,
        })

    @staticmethod
    async def _handle_end_teaching(
        websocket: WebSocket, session_id: int, data: dict[str, Any], controller: Any
    ) -> None:
        cmd = WsEndTeachingCommand(**data)
        result = controller.handle_end_teaching()
        await websocket.send_json({
            "type": "command_result",
            "command": "end_teaching",
            "success": True,
            "session_id": session_id,
            "data": result,
        })


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
    await websocket.send_json(
        {
            "type": "connected",
            "session_id": session_id,
        }
    )

    logger.info("WebSocket 连接建立 (session_id=%d)", session_id)

    try:
        while True:
            data = await websocket.receive_json()

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "pong":
                pass  # 客户端心跳响应
            elif msg_type in _TEACHER_COMMAND_HANDLERS or msg_type == "unknown":
                # 路由到命令处理器
                await _handle_command(websocket, session_id, data)

    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开 (session_id=%d)", session_id)
    except Exception:
        logger.warning("WebSocket 异常 (session_id=%d)", session_id, exc_info=True)
    finally:
        manager.disconnect(session_id=session_id, websocket=websocket)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/units/test_ws_command_router.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add models/session/router_websocket.py tests/units/test_ws_command_router.py
git commit -m "feat(ws): add command routing from WebSocket to TeacherSessionController"
```

---

## Task 4: 观察模式 Orchestrator 初始化与后台运行

**涉及文件：**
- 重写: `backend/models/observation/router.py`
- 新建: `backend/tests/integration/test_observation_api.py` (重写)

- [ ] **Step 1: 编写失败测试**

重写 `backend/tests/integration/test_observation_api.py`：

```python
"""观察模式 API 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def anyio_backend():
    """创建测试用 ASGI transport."""
    transport = ASGITransport(app=app)
    return transport


@pytest.fixture(autouse=True)
def reset_session_registry():
    """每个测试前重置 SessionRegistry."""
    from core.session_registry import SessionRegistry, set_session_registry

    set_session_registry(SessionRegistry())


class TestObservationApiIntegration:
    """观察模式 API 集成测试."""

    @pytest.mark.asyncio
    async def test_start_observation_initializes_orchestrator(self):
        """POST /observation/start 应初始化 SessionOrchestrator 并注册到 SessionRegistry."""
        from core.session_registry import get_session_registry

        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            response = await client.post("/observation/start", json={
                "topic": "Python 变量",
                "teaching_mode": "didactic",
                "checkpoint_count": 1,
                "students": [
                    {
                        "name": "张三",
                        "level": "average",
                        "attitude": "active",
                        "learning_ability": 7,
                    }
                ],
            })

        assert response.status_code == 200
        data = response.json()
        session_id = data["session_id"]
        assert data["status"] == "running"

        # 验证 orchestrator 已注册
        registry = get_session_registry()
        info = registry.get_session_info(session_id)
        assert info is not None
        assert info["mode"] == "observation"
        assert registry.get_orchestrator(session_id) is not None

    @pytest.mark.asyncio
    async def test_start_observation_missing_topic(self):
        """缺少 topic 应返回 422."""
        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            response = await client.post("/observation/start", json={
                "teaching_mode": "didactic",
                "students": [{"name": "张三", "level": "average", "attitude": "active", "learning_ability": 7}],
            })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_observation_empty_students(self):
        """空学生列表应返回 422."""
        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            response = await client.post("/observation/start", json={
                "topic": "Python",
                "teaching_mode": "didactic",
                "students": [],
            })

        assert response.status_code == 422

    @pytest.mark.asyncio
 async def test_start_observation_invalid_mode(self):
        """无效教学模式应返回 422."""
        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            response = await client.post("/observation/start", json={
                "topic": "Python",
                "teaching_mode": "invalid_mode",
                "students": [{"name": "张三", "level": "average", "attitude": "active", "learning_ability": 7}],
            })

        assert response.status_code == 422
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/integration/test_observation_api.py -v`
Expected: FAIL — orchestrator 未注册到 SessionRegistry

- [ ] **Step 3: 重写 observation/router.py**

```python
"""观察模式 API 路由."""

import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import MemoryManager
from agents.student_agent import StudentAgent
from core.checkpoint.persistence_service import CheckpointPlanPersistence
from core.checkpoint.service import CheckpointPlanService
from core.connection_manager import get_connection_manager
from core.database import get_db
from core.llm_client import LLMClient
from core.session_registry import get_session_registry
from models.checkpoint.schemas import CheckpointPlan
from models.observation.schemas import (
    ObservationConfig,
    ObservationStartResponse,
)
from models.session.orchestrator import SessionOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observation", tags=["observation"])


def _create_llm_client() -> LLMClient:
    """创建 LLM 客户端（从配置加载）."""
    from configs.config import settings

    return LLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=0.7,
    )


def _create_teacher_agent(llm: LLMClient, memory_manager: MemoryManager):
    """创建教师 Agent."""
    from agents.teacher_agent import TeacherAgent

    return TeacherAgent(
        llm=llm,
        memory_manager=memory_manager,
        teaching_mode="didactic",
    )


def _create_student_agents(
    students_config: list[dict], llm: LLMClient, memory_manager: MemoryManager
) -> list[StudentAgent]:
    """从配置创建学生 Agent 列表."""
    from schemas.student import StudentProfile

    agents = []
    for s_config in students_config:
        profile = StudentProfile(**s_config)
        agent = StudentAgent(
            session_memory=memory_manager.session_memory,
            llm=llm,
            profile=profile,
        )
        agents.append(agent)
    return agents


def _create_memory_manager(session_id: int, topic: str) -> MemoryManager:
    """创建 MemoryManager."""
    from agents.memories import SessionMemory, TeacherAgentMemory

    session_memory = SessionMemory(session_id=session_id, topic=topic)
    teacher_memory = TeacherAgentMemory()
    return MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)


async def _generate_checkpoint_plan(
    topic: str, teaching_mode: str, checkpoint_count: int, llm: LLMClient
) -> CheckpointPlan:
    """生成检查点计划."""
    service = CheckpointPlanService(llm)
    return await service.generate_plan(topic, teaching_mode, checkpoint_count)


async def _run_orchestrator_background(session_id: int, orchestrator: SessionOrchestrator) -> None:
    """后台运行 orchestrator 自动教学流程."""
    try:
        await orchestrator.run_autonomous_session()
    except Exception as e:
        logger.error("Orchestrator 运行失败 (session_id=%d): %s", session_id, e, exc_info=True)
    finally:
        from core.session_registry import get_session_registry

        get_session_registry().unregister(session_id)
        logger.info("Orchestrator 已清理 (session_id=%d)", session_id)


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    创建 teaching_session 记录，初始化 SessionOrchestrator，
    注册到 SessionRegistry，后台异步运行教学流程。

    Args:
        config: 观察模式配置
        db: 数据库会话
        background_tasks: FastAPI 后台任务

    Returns:
        会话 ID 和状态
    """
    # 创建 teaching_session 记录
    session = TeachingSessionModel(
        topic=config.topic,
        teaching_mode=config.teaching_mode,
        students_config=[s.model_dump() for s in config.students],
    )
    db.add(session)
    await db.flush()
    session_id = session.id
    await db.commit()

    # 初始化 LLM 和 agents
    llm = _create_llm_client()
    memory_manager = _create_memory_manager(session_id, config.topic)
    teacher_agent = _create_teacher_agent(llm, memory_manager)
    student_agents = _create_student_agents(
        [s.model_dump() for s in config.students], llm, memory_manager
    )

    # 生成检查点计划
    checkpoint_plan = await _generate_checkpoint_plan(
        config.topic, config.teaching_mode, config.checkpoint_count, llm
    )

    # 持久化检查点计划
    persistence = CheckpointPlanPersistence(db)
    await persistence.save_plan(session_id, checkpoint_plan)

    # 创建 orchestrator
    orchestrator = SessionOrchestrator(
        teacher_agent=teacher_agent,
        student_agents=student_agents,
        checkpoint_plan=checkpoint_plan,
        memory_manager=memory_manager,
    )

    # 注册到 SessionRegistry（WebSocket 端点可通过 session_id 找到 orchestrator）
    registry = get_session_registry()
    registry.register(session_id=session_id, mode="observation", orchestrator=orchestrator)

    # 后台运行教学流程
    background_tasks.add_task(_run_orchestrator_background, session_id, orchestrator)

    logger.info(
        "观察模式会话启动成功 (session_id=%d, students=%d, checkpoints=%d)",
        session_id,
        len(student_agents),
        len(checkpoint_plan.checkpoints),
    )

    return ObservationStartResponse(
        session_id=session_id,
        status="running",
    )
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/integration/test_observation_api.py -v`
Expected: ALL PASS (4 tests)
注意: 第1个测试需要 LLM API（生成检查点计划），其余测试不需要 LLM。

- [ ] **Step 5: Commit**

```bash
cd backend && git add models/observation/router.py tests/integration/test_observation_api.py
git commit -m "feat(observation): initialize orchestrator with LLM and register to SessionRegistry"
```

---

## Task 5: WebSocket 命令路由集成测试

**涉及文件：**
- 重写: `backend/tests/integration/test_websocket.py`

- [ ] **Step 1: 编写失败测试**

重写 `backend/tests/integration/test_websocket.py`：

```python
"""WebSocket 集成测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
def anyio_backend():
    """创建测试用 ASGI transport."""
    transport = ASGITransport(app=app)
    return transport


@pytest.fixture(autouse=True)
def reset_globals():
    """每个测试前重置全局状态."""
    from core.connection_manager import ConnectionManager, set_connection_manager
    from core.session_registry import SessionRegistry, set_session_registry

    set_connection_manager(ConnectionManager())
    set_session_registry(SessionRegistry())


class TestWebSocketCommandIntegration:
    """WebSocket 命令路由集成测试."""

    @pytest.mark.asyncio
    async def test_broadcast_lecture_command_via_websocket(self):
        """通过 WebSocket 发送 broadcast_lecture 命令，controller 被调用."""
        from unittest.mock import MagicMock, patch

        # 创建 mock controller 并注册
        from core.session_registry import get_session_registry

        mock_controller = MagicMock()
        mock_controller.handle_broadcast_lecture = MagicMock()

        registry = get_session_registry()
        registry.register(session_id=42, mode="teacher", controller=mock_controller)

        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            async with client.websocket_connect("/ws/sessions/42") as ws:
                # 接收 connected 事件
                data = await ws.receive_json()
                assert data["type"] == "connected"

                # 发送命令
                await ws.send_json({
                    "type": "broadcast_lecture",
                    "content": "测试讲授内容",
                })

                # 接收命令结果
                result = await ws.receive_json()
                assert result["type"] == "command_result"
                assert result["command"] == "broadcast_lecture"
                assert result["success"] is True

        # 验证 controller 被调用
        mock_controller.handle_broadcast_lecture.assert_called_once_with("测试讲授内容")

    @pytest.mark.asyncio
    async def test_unknown_command_returns_error_via_websocket(self):
        """发送未知命令类型时返回 error."""
        from core.session_registry import get_session_registry

        mock_controller = MagicMock()
        registry = get_session_registry()
        registry.register(session_id=43, mode="teacher", controller=mock_controller)

        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            async with client.websocket_connect("/ws/sessions/43") as ws:
                data = await ws.receive_json()
                assert data["type"] == "connected"

                await ws.send_json({"type": "invalid_command"})

                result = await ws.receive_json()
                assert result["type"] == "error"
                assert "unknown command" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_command_to_nonexistent_session_returns_error(self):
        """向未注册的 session 发送命令返回 error."""
        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            async with client.websocket_connect("/ws/sessions/999") as ws:
                data = await ws.receive_json()
                assert data["type"] == "connected"

                await ws.send_json({
                    "type": "broadcast_lecture",
                    "content": "测试",
                })

                result = await ws.receive_json()
                assert result["type"] == "error"
                assert "not found" in result["message"].lower()


class TestWebSocketHeartbeat:
    """WebSocket 心跳测试（保留原有测试）."""

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self):
        """ping/pong 心跳机制."""
        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            async with client.websocket_connect("/ws/sessions/1") as ws:
                data = await ws.receive_json()
                assert data["type"] == "connected"

                await ws.send_json({"type": "ping"})
                response = await ws.receive_json()
                assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_websocket_connect_and_receive_connected_event(self):
        """连接后收到 connected 事件."""
        async with AsyncClient(transport=anyio_backend(), base_url="http://test") as client:
            async with client.websocket_connect("/ws/sessions/1") as ws:
                data = await ws.receive_json()
                assert data["type"] == "connected"
                assert "session_id" in data
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/integration/test_websocket.py -v`
Expected: FAIL — 命令路由未实现（WebSocket 端点不路由命令到 controller）

- [ ] **Step 3: 更新测试（已包含 Task 3 的 router_websocket.py 实现，运行即可）**

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/integration/test_websocket.py -v`
Expected: ALL PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add tests/integration/test_websocket.py
git commit -m "test(ws): add command routing integration tests for WebSocket"
```

---

## Task 6: 更新文档

**涉及文件：**
- 修改: `docs/api.md`
- 修改: `docs/tests/backend/index.md`

- [ ] **Step 1: 更新 docs/api.md**

在 WebSocket 通信章节的「服务端推送事件」表格后添加：

```markdown
**客户端 → 服务端命令（教师模式）:**

| 命令类型 | type 字段 | 必填字段 | 说明 |
|---------|-----------|---------|------|
| 广播讲授 | `broadcast_lecture` | `content` | 教师广播讲授内容 |
| 全体提问 | `ask_to_all` | `question` | 向全体学生提问，LLM 生成回答 |
| 指定提问 | `ask_to_student` | `question`, `student_name` | 向指定学生提问 |
| 教师回复 | `teacher_reply` | `reply`, `student_name` | 教师回复学生 |
| 推进检查点 | `advance_checkpoint` | — | 手动推进到下一个检查点 |
| 结束对话 | `end_dialogue` | — | 结束当前对话，触发旁听学习 |
| 布置作业 | `assign_homework` | `content` | 教师布置作业 |
| 收集作业 | `collect_homework` | `homework_prompt` | 收集学生作业 |
| 结束教学 | `end_teaching` | — | 结束教学，收集反馈 |

**命令响应格式:**
```json
{
  "type": "command_result",
  "command": "broadcast_lecture",
  "success": true,
  "session_id": 1,
  "data": { }
}
```

**错误响应格式:**
```json
{
  "type": "error",
  "message": "Session 1 not found",
  "session_id": 1
}
```

**观察模式启动流程更新:**

1. `POST /observation/start` → 创建 DB 记录 → 初始化 LLM/Agents → 生成检查点计划 → 创建 SessionOrchestrator → 注册到 SessionRegistry → 后台运行 `run_autonomous_session()`
2. 前端通过 `/ws/sessions/{session_id}` 连接 → 实时接收教学消息和检查点状态
3. 会话结束后 orchestrator 自动从 SessionRegistry 注销
```

- [ ] **Step 2: 更新 docs/tests/backend/index.md**

添加新测试文件文档：

```markdown
### tests/units/test_ws_command_router.py
WebSocket 命令 schema 验证和命令路由单元测试

- **TestWsCommandSchemas** - WebSocket 命令 schema 验证
  - `test_broadcast_lecture_command_valid()` - 合法的 broadcast_lecture 命令
  - `test_broadcast_lecture_command_missing_content()` - 缺少 content 字段报错
  - `test_ask_to_all_command_valid()` - 合法的 ask_to_all 命令
  - `test_ask_to_student_command_valid()` - 合法的 ask_to_student 命令
  - `test_teacher_reply_command_valid()` - 合法的 teacher_reply 命令
  - `test_advance_checkpoint_command_valid()` - 合法的 advance_checkpoint 命令
  - `test_assign_homework_command_valid()` - 合法的 assign_homework 命令
  - `test_collect_homework_command_valid()` - 合法的 collect_homework 命令
  - `test_end_teaching_command_valid()` - 合法的 end_teaching 命令
  - `test_unknown_command_type_rejected()` - 未知命令类型报错

- **TestWsCommandRouter** - WebSocket 命令路由单元测试
  - `test_broadcast_lecture_routes_to_controller()` - broadcast_lecture 路由到 controller
  - `test_ask_to_all_routes_to_controller()` - ask_to_all 路由到 controller
  - `test_unknown_command_returns_error()` - 未知命令返回 error
  - `test_no_session_returns_error()` - session 不存在返回 error
  - `test_advance_checkpoint_routes_to_controller()` - advance_checkpoint 路由到 controller
  - `test_command_result_pushed_via_websocket()` - 命令结果通过 WebSocket 推送

### tests/integration/test_observation_api.py
观察模式 API 集成测试（含 LLM 调用）

- **TestObservationApiIntegration** - 观察模式 API 集成测试
  - `test_start_observation_initializes_orchestrator()` - 启动会话初始化 orchestrator 并注册
  - `test_start_observation_missing_topic()` - 缺少 topic 返回 422
  - `test_start_observation_empty_students()` - 空学生列表返回 422
  - `test_start_observation_invalid_mode()` - 无效教学模式返回 422

### tests/integration/test_websocket.py
WebSocket 命令路由集成测试

- **TestWebSocketCommandIntegration** - WebSocket 命令路由集成测试
  - `test_broadcast_lecture_command_via_websocket()` - 通过 WS 发送命令验证 controller 被调用
  - `test_unknown_command_returns_error_via_websocket()` - 未知命令返回 error
  - `test_command_to_nonexistent_session_returns_error()` - 未注册 session 返回 error

- **TestWebSocketHeartbeat** - WebSocket 心跳测试（保留）
  - `test_websocket_ping_pong()` - ping/pong 心跳机制
  - `test_websocket_connect_and_receive_connected_event()` - 连接后收到 connected 事件
```

- [ ] **Step 3: Commit**

```bash
cd backend && git add docs/api.md docs/tests/backend/index.md
git commit -m "docs: update WebSocket command docs and test index"
```

---

## 验证清单

完成所有任务后，运行完整测试套件：

```bash
cd backend

# 单元测试（不依赖 LLM）
pytest tests/units/ -v

# WebSocket 集成测试（不依赖 LLM）
pytest tests/integration/test_websocket.py -v

# 会话 API 集成测试（不依赖 LLM）
pytest tests/integration/test_session_api.py -v

# 观察模式 API 集成测试（test_start_observation_initializes_orchestrator 需要 LLM）
pytest tests/integration/test_observation_api.py -v

# 代码质量
ruff check models/session/router_websocket.py models/session/schemas.py core/session_registry.py models/observation/router.py
ruff format models/session/router_websocket.py models/session/schemas.py core/session_registry.py models/observation/router.py
```

**预期结果:**
- 单元测试: 180+ passed
- 集成测试: 13+ passed (其中观察模式初始化测试需要 LLM API)
- Ruff: 0 errors
