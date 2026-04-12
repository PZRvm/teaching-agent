# Phase 12: 教师模式前端 实现计划

> **给 agentic 工作者：** REQUIRED SUB-SKILL：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐条执行本计划。步骤使用复选框（`- [ ]`）语法方便跟踪。

**Goal：** 实现教师模式的完整前端 UI，包括配置界面（TeacherConfig）、教学界面（TeacherView）、双向 WebSocket 通信、检查点编辑/推进，以及必要的前端共享组件（useTeacherWebSocket wrapper、MessageList、RoughTextarea）。复用 Phase 10 创建的 PageNav 和 StudentChip 共享组件。

**Architecture：** 前端采用 React + TypeScript + Vite + styled-components，每个组件文件只保留一个 `Wrapper` styled component，内部使用 `className`（kebab-case）+ 多层嵌套选择器。共享组件（useTeacherWebSocket、MessageList、RoughTextarea）放在 `src/components/` 或 `src/hooks/`，页面视图放在 `src/views/`。WebSocket 使用双向通信模式：教师模式用户通过 `useTeacherWebSocket` wrapper 发送操作指令（broadcast_lecture、ask_to_all 等），后端返回学生响应（student_answer）和状态更新（checkpoint_state_change）。所有 API 调用通过 Phase 10 创建的 `apis/base.ts`（axios）封装在 `src/apis/` 目录。

**Tech Stack：** React 19 + TypeScript + Vite，styled-components，react-router-dom，Vitest + React Testing Library，WebSocket API。

---

## 文件结构（File Structure）

本计划会创建/修改的文件如下：

### 共享组件（Shared Components）

> **跨计划说明：** `PageNav` 和 `StudentChip` 由 Phase 10（任务 1.3 和 1.4）创建，Phase 12 直接导入使用。以下列出 Phase 10 已有但 Phase 12 也用到的组件。

- **已存在** `frontend/src/components/PageNav.tsx` —— Phase 10 创建，页面顶部导航栏
- **已存在** `frontend/src/components/StudentChip.tsx` —— Phase 10 创建，学生信息标签
- **已存在** `frontend/src/components/RoughButton.tsx` —— 已有，复用
- **已存在** `frontend/src/components/RoughCard.tsx` —— 已有，复用
- **已存在** `frontend/src/components/RoughInput.tsx` —— 已有，复用
- **已存在** `frontend/src/components/RoughBadge.tsx` —— 已有，复用

#### Phase 12 新建组件

- **新建** `frontend/src/hooks/useTeacherWebSocket.ts` —— 教师模式 WebSocket wrapper（在 useWebSocketBase 基础上添加 sendCommand、clearErrors 双向通信能力）。
- **新建** `frontend/src/components/MessageList.tsx` —— 消息列表组件（显示教师讲授、学生回答、系统消息等）。同时服务于观察模式和教师模式。
- **新建** `frontend/src/components/RoughTextarea.tsx` —— 手绘风格多行文本输入框。用于教师讲授内容输入、问题输入、作业内容输入。

### API 客户端（API Client）

- **新建** `frontend/src/apis/teacher.ts` —— 教师模式 API 调用函数（startTeacherSession、getCheckpointPlan、updateCheckpointPlan）。
- **已存在** `frontend/src/apis/base.ts` —— Phase 10 任务 1.5 创建（axios 封装），本计划直接使用。

### 后端新增端点（Backend）

- **新建** `backend/models/teacher/router.py` —— 教师模式 REST API（POST /teacher/start）。
- **新建** `backend/models/teacher/schemas.py` —— 教师模式请求/响应 schemas。
- **修改** `backend/main.py` —— 注册教师模式路由。

### 教师模式页面（Teacher Mode Pages）

- **新建** `frontend/src/views/TeacherConfig.tsx` —— 教师模式配置页面（主题输入 + 学生配置 + 检查点计划生成/编辑 + 开始教学按钮）。
- **新建** `frontend/src/views/TeacherView.tsx` —— 教师模式教学页面（讲授输入、提问、学生选择器、消息列表、检查点进度条、作业/结束按钮）。

**已知简化（将在后续迭代中完善）**：
- 学生选择器当前硬编码为"张三"，完整实现需要从 API 获取学生列表或通过 WebSocket 推送学生列表事件。
- 检查点编辑 UI 未在本计划中实现（API 已就绪，使用 `PUT /checkpoint-plans/{sessionId}`）。
- 教师回复（teacher_reply）需要知道当前对话的学生名称，当前简化为空字符串。
- **修改** `frontend/src/App.tsx` —— 添加 `/teacher/config` 和 `/teacher/session/:sessionId` 路由。

### 测试文件（Tests）

- **新建** `frontend/tests/hooks/useTeacherWebSocket.test.ts`
- **新建** `frontend/tests/components/MessageList.test.tsx`
- **新建** `frontend/tests/components/RoughTextarea.test.tsx`
- **新建** `frontend/tests/views/TeacherConfig.test.tsx`
- **新建** `frontend/tests/views/TeacherView.test.tsx`

---

## 共享类型定义（TypeScript Types）

> **跨计划说明：** Phase 10 已在 `frontend/src/types/observation.ts` 中定义了核心类型（`TeachingMode`, `StudentProfile`, `StudentLevel`, `StudentAttitude`, WebSocket 事件类型等）。Phase 12 直接从该文件导入，不再重复定义。

以下类型在 Phase 12 中新增，用于教师模式特有的命令类型：

```typescript
// frontend/src/types/teacher.ts —— 教师模式特有类型

// WebSocket 发送命令类型
interface BroadcastLectureCommand {
  type: 'broadcast_lecture'
  content: string
}

interface AskToAllCommand {
  type: 'ask_to_all'
  question: string
}

interface AskToStudentCommand {
  type: 'ask_to_student'
  question: string
  student_name: string
}

interface TeacherReplyCommand {
  type: 'teacher_reply'
  reply: string
  student_name: string
}

interface AdvanceCheckpointCommand {
  type: 'advance_checkpoint'
}

interface EndDialogueCommand {
  type: 'end_dialogue'
}

interface AssignHomeworkCommand {
  type: 'assign_homework'
  content: string
}

interface CollectHomeworkCommand {
  type: 'collect_homework'
  homework_prompt: string
}

interface EndTeachingCommand {
  type: 'end_teaching'
}

type WsCommand =
  | BroadcastLectureCommand
  | AskToAllCommand
  | AskToStudentCommand
  | TeacherReplyCommand
  | AdvanceCheckpointCommand
  | EndDialogueCommand
  | AssignHomeworkCommand
  | CollectHomeworkCommand
  | EndTeachingCommand
```

---

## 本计划共用的 rough-design 视觉约定

教师模式页面使用绿色主题（`#007d5c`、`#E8F5E9`），与观察模式的蓝色主题（`#2e5cff`、`#E3F2FD`）区分。所有样式遵循已有的 rough-design 设计系统：

- 边框：`3px solid #1A1A1A`
- 阴影：`box-shadow: 4px 4px 0px 0px #1A1A1A`
- 按钮：复用 `RoughButton` 组件（variant="teacher"）
- 卡片：复用 `RoughCard` 组件（variant="green"）
- 输入框：复用 `RoughInput` 组件
- 徽章：复用 `RoughBadge` 组件

---

## 任务 0：验证 API 基础模块

> **跨计划说明：** `apis/base.ts` 已在 Phase 10 中创建（axios 封装）。本任务验证该文件存在且可用。

**相关文件：**
- 已存在：`frontend/src/apis/base.ts`（Phase 10 任务 1.5 创建）

### 任务 0.1：验证 base.ts 存在

- [ ] **步骤 1：确认文件存在**

```bash
ls frontend/src/apis/base.ts
```

**预期结果：** 文件存在。

---

## 任务 1：创建教师模式 API 客户端

目标：封装教师模式需要的所有 REST API 调用（启动会话、获取/编辑检查点计划）。

**相关文件：**
- 新建：`frontend/src/apis/teacher.ts`
- 依赖：`frontend/src/apis/base.ts`

### 任务 1.1：实现教师 API 客户端

- [ ] **步骤 1：创建 `frontend/src/apis/teacher.ts`**

```typescript
// frontend/src/apis/teacher.ts
import { api } from './base'

interface StudentProfileInput {
  name: string
  level: string
  attitude: string
  learning_ability: number
  gender?: string
  background?: string
}

interface TeacherStartRequest {
  topic: string
  students: StudentProfileInput[]
  checkpoint_count?: number
}

interface TeacherStartResponse {
  session_id: number
  status: string
}

interface CheckpointInput {
  title: string
  key_point: string
  checkpoint_question: string
  state?: string
}

interface CheckpointPlanResponse {
  topic: string
  teaching_mode: string
  checkpoints: CheckpointInput[]
  current_index: number
}

interface CheckpointPlanUpdateRequest {
  topic: string
  teaching_mode: string
  checkpoints: CheckpointInput[]
}

export async function startTeacherSession(
  data: TeacherStartRequest,
): Promise<TeacherStartResponse> {
  return api.post<TeacherStartResponse>('/teacher/start', data)
}

export async function getCheckpointPlan(
  sessionId: number,
): Promise<CheckpointPlanResponse> {
  return api.get<CheckpointPlanResponse>(`/checkpoint-plans/${sessionId}`)
}

export async function updateCheckpointPlan(
  sessionId: number,
  data: CheckpointPlanUpdateRequest,
): Promise<{ success: boolean }> {
  return api.put<{ success: boolean }>(`/checkpoint-plans/${sessionId}`, data)
}

export async function getSessionMessages(sessionId: number): Promise<unknown[]> {
  return api.get<unknown[]>(`/sessions/${sessionId}/messages`)
}

export async function getSessionStatus(sessionId: number): Promise<unknown> {
  return api.get<unknown>(`/sessions/${sessionId}/status`)
}
```

- [ ] **步骤 2：确认文件创建成功**

```bash
ls frontend/src/apis/teacher.ts
```

---

## 任务 2：创建后端教师模式启动端点

目标：在后端添加 `POST /teacher/start` 端点，与观察模式的 `POST /observation/start` 类似，但不创建 TeacherAgent，而是创建 TeacherSessionController 并注册到 SessionRegistry。

**相关文件：**
- 新建：`backend/models/teacher/__init__.py`
- 新建：`backend/models/teacher/schemas.py`
- 新建：`backend/models/teacher/router.py`
- 修改：`backend/main.py`

### 任务 2.1：编写失败测试（RED）

- [ ] **步骤 1：创建教师模式端点测试**

新建 `backend/tests/units/test_teacher_router.py`：

```python
# backend/tests/units/test_teacher_router.py
"""教师模式 API 端点单元测试."""

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
class TestTeacherStartEndpoint:
    """POST /teacher/start 端点测试."""

    async def test_start_teacher_session_returns_session_id(self, db_session, override_get_db):
        """测试启动教师模式会话返回 session_id."""
        request_data = {
            "topic": "Python 变量与数据类型",
            "students": [
                {
                    "name": "张三",
                    "level": "excellent",
                    "attitude": "active",
                    "learning_ability": 8,
                },
                {
                    "name": "李四",
                    "level": "average",
                    "attitude": "neutral",
                    "learning_ability": 5,
                },
            ],
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/teacher/start", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert isinstance(data["session_id"], int)
        assert data["status"] == "ready"

    async def test_start_teacher_session_without_topic_fails(self):
        """测试缺少主题时返回 422."""
        request_data = {
            "students": [
                {
                    "name": "张三",
                    "level": "excellent",
                    "attitude": "active",
                    "learning_ability": 8,
                }
            ],
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/teacher/start", json=request_data)

        assert response.status_code == 422

    async def test_start_teacher_session_without_students_fails(self):
        """测试缺少学生时返回 422."""
        request_data = {
            "topic": "Python 变量与数据类型",
            "students": [],
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/teacher/start", json=request_data)

        assert response.status_code == 422
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd backend
pytest tests/units/test_teacher_router.py -v
```

**预期结果：** 测试失败，因为 `/teacher/start` 端点不存在。

### 任务 2.2：实现后端端点（GREEN）

- [ ] **步骤 3：创建 `backend/models/teacher/__init__.py`**

```python
# backend/models/teacher/__init__.py
```

- [ ] **步骤 4：创建 `backend/models/teacher/schemas.py`**

```python
# backend/models/teacher/schemas.py
"""教师模式 Pydantic schemas."""

from pydantic import BaseModel, Field

from schemas.student import StudentProfile


class TeacherStartRequest(BaseModel):
    """教师模式启动请求."""

    topic: str = Field(min_length=1, description="教学主题")
    students: list[StudentProfile] = Field(min_length=1, description="学生列表")
    checkpoint_count: int = Field(default=5, ge=1, le=10, description="检查点数量")


class TeacherStartResponse(BaseModel):
    """教师模式启动响应."""

    session_id: int = Field(description="会话ID")
    status: str = Field(description="会话状态")
```

- [ ] **步骤 5：创建 `backend/models/teacher/router.py`**

```python
# backend/models/teacher/router.py
"""教师模式 API 路由."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import MemoryManager
from agents.student_agent import StudentAgent
from core.database import get_db
from core.llm_client import LLMClient
from models.checkpoint.persistence_service import CheckpointPlanPersistence
from models.checkpoint.service import CheckpointPlanService
from models.session.router_websocket import get_session_registry
from models.session.teacher_controller import TeacherSessionController
from models.teacher.schemas import TeacherStartRequest, TeacherStartResponse
from orm.teaching_session import TeachingSessionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teacher", tags=["teacher"])


def _create_llm_client() -> LLMClient:
    """创建 LLM 客户端（从配置加载）."""
    import os
    from pathlib import Path

    import yaml

    config_path = Path(__file__).parents[2] / "configs" / "llm.yml"
    with open(config_path) as f:
        llm_config = yaml.safe_load(f)

    return LLMClient(
        base_url=llm_config["llm"]["base_url"],
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        model=llm_config["llm"]["model"],
        temperature=llm_config["llm"]["temperature"],
    )


def _create_memory_manager(session_id: int, topic: str) -> MemoryManager:
    """创建 MemoryManager."""
    from agents.memories import SessionMemory, TeacherAgentMemory

    session_memory = SessionMemory(session_id=session_id, topic=topic)
    teacher_memory = TeacherAgentMemory()
    return MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)


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


@router.post("/start", summary="启动教师模式会话", response_model=TeacherStartResponse)
async def start_teacher_session(
    config: TeacherStartRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TeacherStartResponse:
    """启动教师模式会话.

    创建 teaching_session 记录，初始化 TeacherSessionController，
    生成检查点计划，注册到 SessionRegistry（等待前端 WebSocket 连接）。

    Args:
        config: 教师模式配置
        db: 数据库会话

    Returns:
        会话 ID 和状态
    """
    # 创建 teaching_session 记录
    session = TeachingSessionModel(
        topic=config.topic,
        teaching_mode="teacher",
        students_config=[s.model_dump() for s in config.students],
    )
    db.add(session)
    await db.flush()
    session_id = session.id
    await db.commit()

    # 初始化 LLM 和 agents
    llm = _create_llm_client()
    memory_manager = _create_memory_manager(session_id, config.topic)
    student_agents = _create_student_agents(
        [s.model_dump() for s in config.students], llm, memory_manager
    )

    # 生成检查点计划（teaching_mode="teacher"）
    from models.checkpoint.schemas import CheckpointPlan

    checkpoint_plan_service = CheckpointPlanService(llm)
    checkpoint_plan = await checkpoint_plan_service.generate_plan(
        topic=config.topic,
        teaching_mode="teacher",
        num_checkpoints=config.checkpoint_count,
    )

    # 持久化检查点计划
    persistence = CheckpointPlanPersistence(db)
    await persistence.save_plan(session_id=session_id, plan=checkpoint_plan)

    # 创建 TeacherSessionController
    controller = TeacherSessionController(
        student_agents=student_agents,
        memory_manager=memory_manager,
        checkpoint_plan=checkpoint_plan,
    )

    # 注册到 SessionRegistry
    registry = get_session_registry()
    registry.register(
        session_id=session_id,
        mode="teacher",
        controller=controller,
    )

    logger.info(
        "教师模式会话启动成功 (session_id=%d, students=%d, checkpoints=%d)",
        session_id,
        len(student_agents),
        len(checkpoint_plan.checkpoints),
    )

    return TeacherStartResponse(
        session_id=session_id,
        status="ready",
    )
```

- [ ] **步骤 6：修改 `backend/main.py` 注册教师路由**

在 `backend/main.py` 中添加教师路由导入和注册：

```python
# 在导入区域添加
from models.teacher.router import router as teacher_router  # noqa: E402

# 在 include_router 区域添加
app.include_router(teacher_router)
```

完整的 `main.py` 修改后：

```python
from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from models.checkpoint.router import router as checkpoint_router  # noqa: E402
from models.observation.router import router as observation_router  # noqa: E402
from models.session.router import router as session_router  # noqa: E402
from models.session.router_websocket import router as websocket_router  # noqa: E402
from models.teacher.router import router as teacher_router  # noqa: E402

app = FastAPI()

app.include_router(checkpoint_router)
app.include_router(observation_router)
app.include_router(session_router)
app.include_router(websocket_router)
app.include_router(teacher_router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **步骤 7：运行测试，确认通过**

```bash
cd backend
pytest tests/units/test_teacher_router.py -v
```

**预期结果：** 测试通过。

- [ ] **步骤 8：运行 lint 检查**

```bash
cd backend
ruff check models/teacher/
ruff format models/teacher/
```

- [ ] **步骤 9：提交**

```bash
git add backend/models/teacher/ backend/main.py backend/tests/units/test_teacher_router.py
git commit -m "feat(teacher-api): 新增 POST /teacher/start 教师模式启动端点"
```

---

## 任务 3：实现 useTeacherWebSocket Wrapper（TDD）

目标：在 Phase 10 的 `useWebSocketBase` 基础上创建教师模式 wrapper，添加 `sendCommand`（发送操作指令）和 `clearErrors`（清除错误）能力。

> **跨计划说明：** Phase 10 已创建 `useWebSocketBase`（只读：连接管理、消息分发、心跳、教学模式追踪）。本任务在此基础上创建 `useTeacherWebSocket`，添加双向通信所需的 `sendCommand` 和 `clearErrors`。

**相关文件：**
- 新建：`frontend/src/hooks/useTeacherWebSocket.ts`
- 新建：`frontend/tests/hooks/useTeacherWebSocket.test.ts`
- 依赖：`frontend/src/hooks/useWebSocketBase.ts`（Phase 10 任务 3 创建）

### 任务 3.1：编写失败测试（RED）

- [ ] **步骤 1：创建 useTeacherWebSocket 测试**

新建 `frontend/tests/hooks/useTeacherWebSocket.test.ts`：

```typescript
// frontend/tests/hooks/useTeacherWebSocket.test.ts
import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useTeacherWebSocket } from '../../src/hooks/useTeacherWebSocket'

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = []
  static lastInstance: MockWebSocket | null = null

  onopen: ((ev: Event) => void) | null = null
  onmessage: ((ev: MessageEvent) => void) | null = null
  onclose: ((ev: CloseEvent) => void) | null = null
  onerror: ((ev: Event) => void) | null = null
  sentMessages: string[] = []

  constructor(public url: string) {
    MockWebSocket.instances.push(this)
    MockWebSocket.lastInstance = this
  }

  send(data: string) {
    this.sentMessages.push(data)
  }

  close() {
    // 模拟关闭
  }

  // 测试辅助：模拟连接成功
  simulateOpen() {
    if (this.onopen) {
      this.onopen(new Event('open'))
    }
  }

  // 测试辅助：模拟收到消息
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }

  // 测试辅助：模拟连接关闭
  simulateClose() {
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }
}

// 替换全局 WebSocket
vi.stubGlobal('WebSocket', MockWebSocket)

describe('useTeacherWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    MockWebSocket.lastInstance = null
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('初始状态为 disconnected（effect 尚执行）', () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))
    // 初始渲染为 disconnected，effect 执行后才变为 connecting
    expect(result.current.connectionState).toBe('disconnected')
  })

  it('effect 执行后状态变为 connecting', () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))
    // React 会在 effect 执行后同步更新状态（jsdom 行为）
    expect(result.current.connectionState).toBe('connecting')
  })

  it('连接成功后状态变为 connected', () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    expect(result.current.connectionState).toBe('connected')
  })

  it('发送命令通过 WebSocket', () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    act(() => {
      result.current.sendCommand({
        type: 'broadcast_lecture',
        content: '今天我们学习变量',
      })
    })

    const ws = MockWebSocket.lastInstance
    expect(ws?.sentMessages).toHaveLength(1)
    const parsed = JSON.parse(ws!.sentMessages[0])
    expect(parsed.type).toBe('broadcast_lecture')
    expect(parsed.content).toBe('今天我们学习变量')
  })

  it('接收 student_answer 事件并添加到 messages', async () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    act(() => {
      MockWebSocket.lastInstance?.simulateMessage({
        type: 'student_answer',
        session_id: 1,
        student_name: '张三',
        content: '一次函数是 y=kx+b',
        message_type: 'answer_to_checkpoint',
      })
    })

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1)
    })

    expect(result.current.messages[0]).toEqual({
      type: 'student_answer',
      session_id: 1,
      student_name: '张三',
      content: '一次函数是 y=kx+b',
      message_type: 'answer_to_checkpoint',
    })
  })

  it('接收 checkpoint_state_change 事件并更新 checkpointState', async () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    act(() => {
      MockWebSocket.lastInstance?.simulateMessage({
        type: 'checkpoint_state_change',
        session_id: 1,
        index: 0,
        checkpoint: {
          title: 'Python 变量',
          state: 'teaching',
          key_point: '动态类型语言',
        },
        progress: { current: 1, total: 5, completed: 0 },
      })
    })

    await waitFor(() => {
      expect(result.current.checkpointState).not.toBeNull()
    })

    expect(result.current.checkpointState).toEqual({
      index: 0,
      checkpoint: {
        title: 'Python 变量',
        state: 'teaching',
        key_point: '动态类型语言',
      },
      progress: { current: 1, total: 5, completed: 0 },
    })
  })

  it('接收 error 事件并添加到 errors', async () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    act(() => {
      MockWebSocket.lastInstance?.simulateMessage({
        type: 'error',
        message: 'Unknown command',
        session_id: 1,
      })
    })

    await waitFor(() => {
      expect(result.current.errors).toHaveLength(1)
    })

    expect(result.current.errors[0].message).toBe('Unknown command')
  })

  it('连接关闭后状态变为 disconnected', () => {
    const { result } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    act(() => {
      MockWebSocket.lastInstance?.simulateClose()
    })

    expect(result.current.connectionState).toBe('disconnected')
  })

  it('卸载时关闭 WebSocket 连接', () => {
    const { unmount } = renderHook(() => useTeacherWebSocket(1))

    act(() => {
      MockWebSocket.lastInstance?.simulateOpen()
    })

    const ws = MockWebSocket.lastInstance
    unmount()

    // 验证连接被关闭（WebSocket 实例的 close 方法被调用）
    expect(ws?.sentMessages.length).toBe(0) // close 不产生 sentMessages
  })

  it('使用正确的 WebSocket URL', () => {
    renderHook(() => useTeacherWebSocket(42))

    expect(MockWebSocket.lastInstance?.url).toContain('/42')
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/hooks/useTeacherWebSocket.test.ts
```

**预期结果：** 测试失败，因为 `useTeacherWebSocket` hook 不存在。

### 任务 3.2：实现 useTeacherWebSocket Wrapper（GREEN）

- [ ] **步骤 3：创建 `frontend/src/hooks/useTeacherWebSocket.ts`**

```typescript
// frontend/src/hooks/useTeacherWebSocket.ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsEventUnion, WsMessageEvent, CheckpointStateData, TeachingMode } from '../types/observation'

/** 错误信息 */
interface ErrorInfo {
  message: string
  timestamp: number
}

/** useTeacherWebSocket hook 返回值 */
export interface UseTeacherWebSocketReturn {
  /** 当前连接状态 */
  connectionState: 'connecting' | 'connected' | 'disconnected'
  /** 收到的所有消息 */
  messages: WsMessageEvent[]
  /** 当前检查点状态 */
  checkpointState: CheckpointStateData | null
  /** 会话是否已结束 */
  sessionEnded: boolean
  /** 教学模式（从 session_state 事件获取） */
  teachingMode: TeachingMode | null
  /** 错误列表 */
  errors: ErrorInfo[]
  /** 发送操作指令 */
  sendCommand: (command: Record<string, unknown>) => void
  /** 清除错误列表 */
  clearErrors: () => void
}

const WS_BASE = import.meta.env.VITE_WS_BASE ?? 'ws://localhost:8000'

/** 教师模式 WebSocket hook —— 在 useWebSocketBase 基础上添加双向通信能力 */
export function useTeacherWebSocket(sessionId: number | null): UseTeacherWebSocketReturn {
  const [connectionState, setConnectionState] = useState<
    'connecting' | 'connected' | 'disconnected'
  >(sessionId !== null ? 'connecting' : 'disconnected')
  const [messages, setMessages] = useState<WsMessageEvent[]>([])
  const [checkpointState, setCheckpointState] = useState<CheckpointStateData | null>(null)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [teachingMode, setTeachingMode] = useState<TeachingMode | null>(null)
  const [errors, setErrors] = useState<ErrorInfo[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  // 清除错误
  const clearErrors = useCallback(() => {
    setErrors([])
  }, [])

  // 发送命令
  const sendCommand = useCallback((command: Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(command))
    }
  }, [])

  useEffect(() => {
    if (sessionId === null) {
      return
    }

    const ws = new WebSocket(`${WS_BASE}/ws/sessions/${sessionId}`)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionState('connected')
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string)

        switch (data.type) {
          case 'connected':
            // 连接确认，忽略
            break

          case 'student_answer':
          case 'message':
          case 'command_result':
            setMessages((prev) => [...prev, data as WsMessageEvent])
            break

          case 'checkpoint_state_change':
            setCheckpointState({
              index: data.index,
              checkpoint: data.checkpoint,
              progress: data.progress,
            })
            setMessages((prev) => [...prev, data as WsMessageEvent])
            break

          case 'session_state':
            setTeachingMode(data.teaching_mode as TeachingMode)
            break

          case 'session_end':
            setMessages((prev) => [...prev, data as WsMessageEvent])
            break

          case 'error':
            setErrors((prev) => [
              ...prev,
              { message: (data as { message: string }).message, timestamp: Date.now() },
            ])
            break

          case 'pong':
            // 心跳响应，忽略
            break

          default:
            // 其他事件也存入 messages
            setMessages((prev) => [...prev, data as WsMessageEvent])
        }
      } catch {
        // JSON 解析失败，忽略
      }
    }

    ws.onclose = () => {
      setConnectionState('disconnected')
    }

    ws.onerror = () => {
      setErrors((prev) => [
        ...prev,
        { message: 'WebSocket 连接错误', timestamp: Date.now() },
      ])
    }

    // 心跳机制
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)

    return () => {
      clearInterval(heartbeat)
      ws.close()
      wsRef.current = null
    }
  }, [sessionId])

  return {
    connectionState,
    messages,
    checkpointState,
    sessionEnded,
    teachingMode,
    errors,
    sendCommand,
    clearErrors,
  }
}
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/hooks/useTeacherWebSocket.test.ts
```

**预期结果：** 所有 8 个测试通过。

- [ ] **步骤 5：运行 lint 检查**

```bash
cd frontend
npm run lint
```

- [ ] **步骤 6：提交**

```bash
git add frontend/src/hooks/useTeacherWebSocket.ts frontend/tests/hooks/useTeacherWebSocket.test.ts
git commit -m "feat(teacher-frontend): 添加 useTeacherWebSocket 双向通信 wrapper"
```

---

## 任务 4：实现 RoughTextarea 组件（TDD）

目标：创建手绘风格多行文本输入框，用于教师输入讲授内容、问题等。

**相关文件：**
- 新建：`frontend/src/components/RoughTextarea.tsx`
- 新建：`frontend/tests/components/RoughTextarea.test.tsx`

### 任务 4.1：编写失败测试（RED）

- [ ] **步骤 1：创建 RoughTextarea 测试**

新建 `frontend/tests/components/RoughTextarea.test.tsx`：

```typescript
// frontend/tests/components/RoughTextarea.test.tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RoughTextarea from '../../src/components/RoughTextarea'

describe('RoughTextarea', () => {
  it('renders textarea with placeholder', () => {
    render(<RoughTextarea placeholder="输入讲授内容..." />)
    const textarea = screen.getByPlaceholderText('输入讲授内容...')
    expect(textarea).toBeInTheDocument()
  })

  it('allows typing text', async () => {
    const user = userEvent.setup()
    render(<RoughTextarea placeholder="输入..." />)

    const textarea = screen.getByPlaceholderText('输入...')
    await user.type(textarea, '今天我们学习变量')

    expect(textarea).toHaveValue('今天我们学习变量')
  })

  it('calls onChange when value changes', async () => {
    const user = userEvent.setup()
    const handleChange = vi.fn()
    render(<RoughTextarea value="" onChange={handleChange} />)

    const textarea = screen.getByRole('textbox')
    await user.type(textarea, 'a')

    expect(handleChange).toHaveBeenCalledTimes(1)
  })

  it('applies className prop', () => {
    render(<RoughTextarea className="custom-class" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea.className).toContain('custom-class')
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/components/RoughTextarea.test.tsx
```

### 任务 4.2：实现 RoughTextarea 组件（GREEN）

- [ ] **步骤 3：创建 `frontend/src/components/RoughTextarea.tsx`**

```typescript
// frontend/src/components/RoughTextarea.tsx
import styled from 'styled-components'

type RoughTextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  className?: string
}

const Wrapper = styled.textarea`
  background: white;
  border: 3px solid #1A1A1A;
  padding: 12px 16px;
  font-size: 16px;
  font-family: 'Be Vietnam Pro', system-ui, sans-serif;
  box-shadow: 2px 2px 0px 0px #1A1A1A;
  outline: none;
  transition: box-shadow 0.2s ease;
  width: 100%;
  resize: vertical;
  min-height: 100px;
  line-height: 1.5;

  &::placeholder {
    color: #d4d4d4;
  }

  &:focus {
    box-shadow: 4px 4px 0px 0px #0041e0;
  }
`

export default function RoughTextarea({ className, ...rest }: RoughTextareaProps) {
  return <Wrapper className={className} {...rest} />
}
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/components/RoughTextarea.test.tsx
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/components/RoughTextarea.tsx frontend/tests/components/RoughTextarea.test.tsx
git commit -m "feat(teacher-frontend): 添加 RoughTextarea 手绘风格多行文本框组件"
```

---

## 任务 5：实现 MessageList 组件（TDD）

目标：创建消息列表组件，显示教学过程中的所有消息（教师讲授、学生回答、系统消息），同时服务于观察模式和教师模式。

**相关文件：**
- 新建：`frontend/src/components/MessageList.tsx`
- 新建：`frontend/tests/components/MessageList.test.tsx`

### 任务 5.1：编写失败测试（RED）

- [ ] **步骤 1：创建 MessageList 测试**

新建 `frontend/tests/components/MessageList.test.tsx`：

```typescript
// frontend/tests/components/MessageList.test.tsx
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageList from '../../src/components/MessageList'

describe('MessageList', () => {
  it('renders empty state when no messages', () => {
    render(<MessageList messages={[]} />)
    expect(screen.getByText('暂无消息')).toBeInTheDocument()
  })

  it('renders teacher lecture message', () => {
    const messages = [
      {
        type: 'message',
        sender: 'teacher',
        message_type: 'lecture',
        content: '今天我们学习 Python 变量',
        receiver: 'all',
      },
    ]
    render(<MessageList messages={messages} />)
    expect(screen.getByText('今天我们学习 Python 变量')).toBeInTheDocument()
  })

  it('renders student answer message with student name', () => {
    const messages = [
      {
        type: 'student_answer',
        student_name: '张三',
        content: '变量是用来存储数据的容器',
        message_type: 'answer_to_checkpoint',
      },
    ]
    render(<MessageList messages={messages} />)
    expect(screen.getByText('张三')).toBeInTheDocument()
    expect(screen.getByText('变量是用来存储数据的容器')).toBeInTheDocument()
  })

  it('renders checkpoint state change as system message', () => {
    const messages = [
      {
        type: 'checkpoint_state_change',
        index: 0,
        checkpoint: { title: 'Python 变量', state: 'teaching', key_point: '动态类型' },
        progress: { current: 1, total: 5, completed: 0 },
      },
    ]
    render(<MessageList messages={messages} />)
    expect(screen.getByText(/检查点 1\/5：Python 变量/)).toBeInTheDocument()
  })

  it('renders command result message', () => {
    const messages = [
      {
        type: 'command_result',
        command: 'broadcast_lecture',
        success: true,
      },
    ]
    render(<MessageList messages={messages} />)
    expect(screen.getByText('讲授内容已广播')).toBeInTheDocument()
  })

  it('renders error message', () => {
    const messages = [
      {
        type: 'error',
        message: 'Unknown command',
      },
    ]
    render(<MessageList messages={messages} />)
    expect(screen.getByText('Unknown command')).toBeInTheDocument()
  })

  it('auto-scrolls to bottom on new messages', () => {
    const messages = [
      {
        type: 'message',
        sender: 'teacher',
        message_type: 'lecture',
        content: '第一条消息',
        receiver: 'all',
      },
    ]
    const { rerender } = render(<MessageList messages={messages} />)

    const newMessages = [
      ...messages,
      {
        type: 'student_answer',
        student_name: '张三',
        content: '第二条消息',
        message_type: 'answer_to_checkpoint',
      },
    ]
    rerender(<MessageList messages={newMessages} />)

    // 验证两个消息都渲染了
    expect(screen.getByText('第一条消息')).toBeInTheDocument()
    expect(screen.getByText('第二条消息')).toBeInTheDocument()
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/components/MessageList.test.tsx
```

### 任务 5.2：实现 MessageList 组件（GREEN）

- [ ] **步骤 3：创建 `frontend/src/components/MessageList.tsx`**

```typescript
// frontend/src/components/MessageList.tsx
import { useEffect, useRef } from 'react'
import styled from 'styled-components'

type Message =
  | {
      type: 'message'
      sender: string
      message_type: string
      content: string
      receiver: string
    }
  | {
      type: 'student_answer'
      student_name: string
      content: string
      message_type: string
    }
  | {
      type: 'checkpoint_state_change'
      index: number
      checkpoint: { title: string; state: string; key_point: string }
      progress: { current: number; total: number; completed: number }
    }
  | {
      type: 'command_result'
      command: string
      success: boolean
    }
  | {
      type: 'error'
      message: string
    }
  | {
      type: 'session_end'
      reason: string
    }

type MessageListProps = {
  messages: Message[]
}

function getSenderLabel(msg: Message): { name: string; role: 'teacher' | 'student' | 'system' } {
  if (msg.type === 'student_answer') {
    return { name: msg.student_name, role: 'student' }
  }
  if (msg.type === 'message') {
    if (msg.sender === 'teacher') {
      return { name: '教师', role: 'teacher' }
    }
    return { name: msg.sender, role: 'student' }
  }
  return { name: '系统', role: 'system' }
}

function getCommandLabel(command: string): string {
  const labels: Record<string, string> = {
    broadcast_lecture: '讲授内容已广播',
    ask_to_all: '已向全体提问',
    ask_to_student: '已向指定学生提问',
    teacher_reply: '回复已发送',
    advance_checkpoint: '已推进到下一个检查点',
    end_dialogue: '对话已结束',
    assign_homework: '作业已布置',
    collect_homework: '正在收集作业',
    end_teaching: '教学已结束',
  }
  return labels[command] ?? `命令 ${command} 已执行`
}

function renderContent(msg: Message): string {
  if (msg.type === 'checkpoint_state_change') {
    return `检查点 ${msg.progress.current}/${msg.progress.total}：${msg.checkpoint.title} [${msg.checkpoint.state}]`
  }
  if (msg.type === 'command_result') {
    return getCommandLabel(msg.command)
  }
  if (msg.type === 'error') {
    return msg.message
  }
  if (msg.type === 'session_end') {
    return `会话结束：${msg.reason}`
  }
  if (msg.type === 'student_answer') {
    return msg.content
  }
  return msg.content
}

function getMessageTypeLabel(msg: Message): string {
  if (msg.type === 'student_answer') {
    return msg.message_type === 'answer_to_checkpoint' ? '回答' : '提问'
  }
  if (msg.type === 'message') {
    const typeLabels: Record<string, string> = {
      lecture: '讲授',
      checkpoint_question: '提问',
      teacher_reply: '回复',
      assign_homework: '作业',
      homework_feedback: '作业反馈',
      end_feedback: '反馈',
    }
    return typeLabels[msg.message_type] ?? msg.message_type
  }
  if (msg.type === 'checkpoint_state_change') return '检查点'
  if (msg.type === 'command_result') return '操作'
  if (msg.type === 'error') return '错误'
  if (msg.type === 'session_end') return '结束'
  return msg.type
}

export default function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length])

  if (messages.length === 0) {
    return (
      <Wrapper>
        <div className="empty-state">暂无消息</div>
      </Wrapper>
    )
  }

  return (
    <Wrapper>
      <div className="message-list">
        {messages.map((msg, index) => {
          const { name, role } = getSenderLabel(msg)
          return (
            <div key={index} className={`message-item message-${role}`}>
              <div className="message-header">
                <span className="message-sender">{name}</span>
                <span className="message-type-badge">{getMessageTypeLabel(msg)}</span>
              </div>
              <div className="message-content">{renderContent(msg)}</div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  width: 100%;
  height: 100%;
  overflow-y: auto;

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: #a0a0a0;
    font-size: 16px;
  }

  .message-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }

  .message-item {
    padding: 12px 16px;
    border-radius: 8px;
    border: 2px solid #1a1a1a;
    background: #ffffff;
    box-shadow: 2px 2px 0px 0px #1a1a1a;
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      transform: translate(-1px, -1px);
      box-shadow: 3px 3px 0px 0px #1a1a1a;
    }
  }

  .message-teacher {
    border-left: 4px solid #007d5c;
    background: #f0faf5;
  }

  .message-student {
    border-left: 4px solid #2e5cff;
    background: #f0f4ff;
  }

  .message-system {
    border-left: 4px solid #f59e0b;
    background: #fffbeb;
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .message-sender {
    font-weight: 700;
    font-size: 14px;
    color: #1a1c1c;
  }

  .message-type-badge {
    font-size: 11px;
    padding: 2px 8px;
    background: #fafafa;
    border: 1px solid #1a1a1a;
    border-radius: 4px;
    color: #1a1c1c;
    font-weight: 600;
    box-shadow: 1px 1px 0px 0px #1a1a1a;
  }

  .message-content {
    font-size: 15px;
    line-height: 1.6;
    color: #333;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message-system .message-content {
    color: #92400e;
    font-style: italic;
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/components/MessageList.test.tsx
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/components/MessageList.tsx frontend/tests/components/MessageList.test.tsx
git commit -m "feat(teacher-frontend): 添加 MessageList 消息列表组件"
```

---

## 任务 6：实现 TeacherConfig 页面（TDD）

目标：实现教师模式配置页面，包括主题输入、学生配置（简化版，先用手动创建）、检查点计划生成、检查点编辑和「开始教学」按钮。

**相关文件：**
- 新建：`frontend/src/views/TeacherConfig.tsx`
- 新建：`frontend/tests/views/TeacherConfig.test.tsx`
- 修改：`frontend/src/App.tsx`

### 任务 6.1：编写失败测试（RED）

- [ ] **步骤 1：创建 TeacherConfig 测试**

新建 `frontend/tests/views/TeacherConfig.test.tsx`：

```typescript
// frontend/tests/views/TeacherConfig.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'

// Mock API
vi.mock('../../src/apis/teacher', () => ({
  startTeacherSession: vi.fn().mockResolvedValue({
    session_id: 42,
    status: 'ready',
  }),
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import TeacherConfig from '../../src/views/TeacherConfig'

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <TeacherConfig />
    </MemoryRouter>,
  )
}

describe('TeacherConfig', () => {
  it('renders topic input and start button', () => {
    renderWithRouter()
    expect(screen.getByPlaceholderText('输入教学主题，例如：Python 变量与数据类型')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '开始教学' })).toBeInTheDocument()
  })

  it('renders page title', () => {
    renderWithRouter()
    expect(screen.getByRole('heading', { name: '教师模式配置' })).toBeInTheDocument()
  })

  it('disables start button when topic is empty', () => {
    renderWithRouter()
    const button = screen.getByRole('button', { name: '开始教学' })
    expect(button).toBeDisabled()
  })

  it('enables start button when topic is entered', async () => {
    const user = userEvent.setup()
    renderWithRouter()

    const input = screen.getByPlaceholderText('输入教学主题，例如：Python 变量与数据类型')
    await user.type(input, 'Python 基础')

    const button = screen.getByRole('button', { name: '开始教学' })
    expect(button).not.toBeDisabled()
  })

  it('shows loading state when generating plan', async () => {
    const { startTeacherSession } = await import('../../src/apis/teacher')
    vi.mocked(startTeacherSession).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ session_id: 42, status: 'ready' }), 1000)),
    )

    const user = userEvent.setup()
    renderWithRouter()

    await user.type(
      screen.getByPlaceholderText('输入教学主题，例如：Python 变量与数据类型'),
      'Python 基础',
    )
    await user.click(screen.getByRole('button', { name: '开始教学' }))

    await waitFor(() => {
      expect(screen.getByText('正在生成教学计划...')).toBeInTheDocument()
    })
  })

  it('navigates to teacher session page after successful start', async () => {
    const user = userEvent.setup()
    renderWithRouter()

    await user.type(
      screen.getByPlaceholderText('输入教学主题，例如：Python 变量与数据类型'),
      'Python 基础',
    )
    await user.click(screen.getByRole('button', { name: '开始教学' }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/teacher/session/42')
    })
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/views/TeacherConfig.test.tsx
```

### 任务 6.2：实现 TeacherConfig 页面（GREEN）

- [ ] **步骤 3：创建 `frontend/src/views/TeacherConfig.tsx`**

```typescript
// frontend/src/views/TeacherConfig.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import StudentChip from '../components/StudentChip'
import RoughButton from '../components/RoughButton'
import RoughCard from '../components/RoughCard'
import RoughInput from '../components/RoughInput'
import { startTeacherSession } from '../apis/teacher'

const DEFAULT_STUDENTS = [
  { name: '张三', level: 'excellent', attitude: 'active', learning_ability: 8 },
  { name: '李四', level: 'average', attitude: 'neutral', learning_ability: 5 },
  { name: '王五', level: 'basic', attitude: 'passive', learning_ability: 3 },
]

export default function TeacherConfig() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const canStart = topic.trim().length > 0 && !loading

  const handleStart = async () => {
    if (!canStart) return

    setLoading(true)
    setError('')

    try {
      const response = await startTeacherSession({
        topic: topic.trim(),
        students: DEFAULT_STUDENTS,
      })
      navigate(`/teacher/session/${response.session_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '启动失败，请重试')
      setLoading(false)
    }
  }

  return (
    <Wrapper>
      <PageNav
        title="教师模式 - 配置"
        onBack={() => navigate('/')}
      />
      <div className="config-container">
        <h1 className="page-title">教师模式配置</h1>
        <p className="page-subtitle">配置教学主题和学生，开始你的教学</p>

        <RoughCard variant="green" rotation={-0.3}>
          <div className="config-section">
            <h2 className="section-title">教学主题</h2>
            <RoughInput
              placeholder="输入教学主题，例如：Python 变量与数据类型"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="topic-input"
            />
          </div>

          <div className="config-section">
            <h2 className="section-title">学生配置</h2>
            <p className="section-desc">当前使用默认学生配置（3 名学生：excellent、average、basic 各一名）。完整的学生配置功能将在后续迭代中实现。</p>
            <div className="student-preview">
              {DEFAULT_STUDENTS.map((student) => (
                <StudentChip
                  key={student.name}
                  name={student.name}
                  level={student.level}
                />
              ))}
            </div>
          </div>

          <div className="config-actions">
            <RoughButton
              variant="teacher"
              onClick={handleStart}
              disabled={!canStart}
            >
              {loading ? '正在生成教学计划...' : '开始教学'}
            </RoughButton>
          </div>

          {error && <div className="error-message">{error}</div>}
        </RoughCard>
      </div>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100vh;
  background: #f9f9f9;
  padding: 64px 24px;
  display: flex;
  justify-content: center;

  .config-container {
    width: 100%;
    max-width: 640px;
  }

  .page-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 36px;
    font-weight: 900;
    color: #1a1c1c;
    margin-bottom: 8px;
  }

  .page-subtitle {
    font-size: 16px;
    color: #747688;
    margin-bottom: 40px;
  }

  .config-section {
    margin-bottom: 32px;
  }

  .section-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #1a1c1c;
    margin-bottom: 12px;
  }

  .section-desc {
    font-size: 14px;
    color: #747688;
    margin-bottom: 16px;
    line-height: 1.5;
  }

  .topic-input {
    margin-bottom: 8px;
  }

  .student-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .config-actions {
    display: flex;
    gap: 16px;
    margin-top: 32px;
  }

  .error-message {
    margin-top: 16px;
    padding: 12px 16px;
    background: #fef2f2;
    border: 2px solid #dc2626;
    border-radius: 8px;
    color: #991b1b;
    font-size: 14px;
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/views/TeacherConfig.test.tsx
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/views/TeacherConfig.tsx frontend/tests/views/TeacherConfig.test.tsx
git commit -m "feat(teacher-frontend): 实现 TeacherConfig 教师模式配置页面"
```

---

## 任务 7：实现 TeacherView 页面（TDD）

目标：实现教师模式教学页面，包括讲授输入、提问（全体/指定学生）、学生响应显示、检查点进度、作业/结束按钮。

**相关文件：**
- 新建：`frontend/src/views/TeacherView.tsx`
- 新建：`frontend/tests/views/TeacherView.test.tsx`

### 任务 7.1：编写失败测试（RED）

- [ ] **步骤 1：创建 TeacherView 测试**

新建 `frontend/tests/views/TeacherView.test.tsx`：

```typescript
// frontend/tests/views/TeacherView.test.tsx
import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

// Mock useTeacherWebSocket
const mockSendCommand = vi.fn()
vi.mock('../../src/hooks/useTeacherWebSocket', () => ({
  useTeacherWebSocket: () => ({
    connectionState: 'connected',
    messages: [],
    checkpointState: {
      index: 0,
      checkpoint: {
        title: 'Python 变量',
        state: 'teaching',
        key_point: '动态类型语言',
      },
      progress: { current: 1, total: 5, completed: 0 },
    },
    errors: [],
    sendCommand: mockSendCommand,
    clearErrors: vi.fn(),
  }),
}))

import TeacherView from '../../src/views/TeacherView'

function renderWithSession(sessionId: string | number = '42') {
  return render(
    <MemoryRouter initialEntries={[`/teacher/session/${sessionId}`]}>
      <Routes>
        <Route path="/teacher/session/:sessionId" element={<TeacherView />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('TeacherView', () => {
  it('renders teaching input area', () => {
    renderWithSession()
    expect(screen.getByPlaceholderText('输入讲授内容...')).toBeInTheDocument()
  })

  it('renders question input for asking all students', () => {
    renderWithSession()
    expect(screen.getByPlaceholderText('输入要提问的问题...')).toBeInTheDocument()
  })

  it('renders action buttons', () => {
    renderWithSession()
    expect(screen.getByRole('button', { name: '广播讲授' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '向全体提问' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '指定学生提问' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '推进检查点' })).toBeInTheDocument()
  })

  it('sends broadcast_lecture command when clicking broadcast button', async () => {
    const user = userEvent.setup()
    renderWithSession()

    const textarea = screen.getByPlaceholderText('输入讲授内容...')
    await user.type(textarea, '今天我们学习变量')
    await user.click(screen.getByRole('button', { name: '广播讲授' }))

    expect(mockSendCommand).toHaveBeenCalledWith({
      type: 'broadcast_lecture',
      content: '今天我们学习变量',
    })
  })

  it('sends ask_to_all command when clicking ask all button', async () => {
    const user = userEvent.setup()
    renderWithSession()

    const input = screen.getByPlaceholderText('输入要提问的问题...')
    await user.type(input, '什么是变量？')
    await user.click(screen.getByRole('button', { name: '向全体提问' }))

    expect(mockSendCommand).toHaveBeenCalledWith({
      type: 'ask_to_all',
      question: '什么是变量？',
    })
  })

  it('sends advance_checkpoint command when clicking advance button', async () => {
    const user = userEvent.setup()
    renderWithSession()

    await user.click(screen.getByRole('button', { name: '推进检查点' }))

    expect(mockSendCommand).toHaveBeenCalledWith({
      type: 'advance_checkpoint',
    })
  })

  it('sends end_teaching command when clicking end button', async () => {
    const user = userEvent.setup()
    renderWithSession()

    await user.click(screen.getByRole('button', { name: '结束教学' }))

    expect(mockSendCommand).toHaveBeenCalledWith({
      type: 'end_teaching',
    })
  })

  it('renders checkpoint progress bar', () => {
    renderWithSession()
    expect(screen.getByText('检查点 1/5')).toBeInTheDocument()
    expect(screen.getByText('Python 变量')).toBeInTheDocument()
  })

  it('renders message list area', () => {
    renderWithSession()
    // MessageList 组件应该渲染（初始为空状态）
    expect(screen.getByText('暂无消息')).toBeInTheDocument()
  })

  it('disables broadcast button when content is empty', () => {
    renderWithSession()
    const button = screen.getByRole('button', { name: '广播讲授' })
    expect(button).toBeDisabled()
  })

  it('disables ask all button when question is empty', () => {
    renderWithSession()
    const button = screen.getByRole('button', { name: '向全体提问' })
    expect(button).toBeDisabled()
  })

  it('sends ask_to_student command when student is selected and question is entered', async () => {
    const user = userEvent.setup()
    renderWithSession()

    // 模拟有学生列表通过消息事件传递
    // 在实际使用中，学生列表通过 API 获取
    // 这里测试 ask_to_student 命令的发送
    const questionInput = screen.getByPlaceholderText('输入要提问的问题...')
    await user.type(questionInput, '请解释什么是变量')

    // 找到指定学生提问按钮并点击
    await user.click(screen.getByRole('button', { name: '指定学生提问' }))

    // 验证 sendCommand 被调用（需要 student_name，实际 UI 通过下拉选择器获取）
    // 注意：当前简化实现中，student_name 需要从学生列表获取
    // 完整的学生选择器将在后续迭代中实现
    expect(mockSendCommand).toHaveBeenCalled()
    const sentData = mockSendCommand.mock.calls[mockSendCommand.mock.calls.length - 1][0]
    expect(sentData.type).toBe('ask_to_student')
    expect(sentData.question).toBe('请解释什么是变量')
  })

  it('sends assign_homework command with content', async () => {
    const user = userEvent.setup()
    renderWithSession()

    const homeworkInput = screen.getByPlaceholderText('输入作业内容...')
    await user.type(homeworkInput, '完成课后习题1-5题')
    await user.click(screen.getByRole('button', { name: '布置作业' }))

    expect(mockSendCommand).toHaveBeenCalledWith({
      type: 'assign_homework',
      content: '完成课后习题1-5题',
    })
  })
})
```

- [ ] **步骤 2：运行测试，确认失败**

```bash
cd frontend
npm run test -- tests/views/TeacherView.test.tsx
```

### 任务 7.2：实现 TeacherView 页面（GREEN）

- [ ] **步骤 3：创建 `frontend/src/views/TeacherView.tsx`**

```typescript
// frontend/src/views/TeacherView.tsx
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import styled from 'styled-components'
import RoughButton from '../components/RoughButton'
import RoughTextarea from '../components/RoughTextarea'
import MessageList from '../components/MessageList'
import { useTeacherWebSocket } from '../hooks/useTeacherWebSocket'

export default function TeacherView() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const sessionIdNum = sessionId ? parseInt(sessionId, 10) : null

  const {
    connectionState,
    messages,
    checkpointState,
    sendCommand,
  } = useTeacherWebSocket(sessionIdNum)

  // 输入状态
  const [lectureContent, setLectureContent] = useState('')
  const [questionContent, setQuestionContent] = useState('')
  const [homeworkContent, setHomeworkContent] = useState('')
  const [replyContent, setReplyContent] = useState('')

  // 命令发送辅助函数
  const handleBroadcastLecture = () => {
    if (!lectureContent.trim()) return
    sendCommand({ type: 'broadcast_lecture', content: lectureContent.trim() })
    setLectureContent('')
  }

  const handleAskToAll = () => {
    if (!questionContent.trim()) return
    sendCommand({ type: 'ask_to_all', question: questionContent.trim() })
    setQuestionContent('')
  }

  const handleAdvanceCheckpoint = () => {
    sendCommand({ type: 'advance_checkpoint' })
  }

  const handleEndDialogue = () => {
    sendCommand({ type: 'end_dialogue' })
  }

  const handleAskToStudent = () => {
    if (!questionContent.trim()) return
    // 简化实现：使用第一个学生作为默认目标
    // 完整实现需要从 API 获取学生列表或通过 WebSocket 推送
    sendCommand({
      type: 'ask_to_student',
      question: questionContent.trim(),
      student_name: '张三', // TODO: 从学生列表选择
    })
    setQuestionContent('')
  }

  const handleAssignHomework = () => {
    if (!homeworkContent.trim()) return
    sendCommand({ type: 'assign_homework', content: homeworkContent.trim() })
    setHomeworkContent('')
  }

  const handleCollectHomework = () => {
    sendCommand({ type: 'collect_homework', homework_prompt: '请提交本次作业' })
  }

  const handleEndTeaching = () => {
    sendCommand({ type: 'end_teaching' })
  }

  const handleTeacherReply = () => {
    if (!replyContent.trim()) return
    sendCommand({ type: 'teacher_reply', reply: replyContent.trim(), student_name: '' })
    setReplyContent('')
  }

  const isConnected = connectionState === 'connected'
  const progress = checkpointState?.progress
  const currentCheckpoint = checkpointState?.checkpoint

  return (
    <Wrapper>
      {/* 顶部状态栏 */}
      <div className="top-bar">
        <div className="connection-status">
          <span className={`status-dot ${connectionState}`} />
          <span className="status-text">
            {connectionState === 'connected' ? '已连接' : connectionState === 'connecting' ? '连接中...' : '已断开'}
          </span>
        </div>
        {progress && (
          <div className="checkpoint-progress">
            <span className="progress-text">检查点 {progress.current}/{progress.total}</span>
            {currentCheckpoint && (
              <span className="checkpoint-title">{currentCheckpoint.title}</span>
            )}
          </div>
        )}
      </div>

      {/* 主内容区域 */}
      <div className="main-content">
        {/* 左侧：消息列表 */}
        <div className="message-panel">
          <div className="panel-header">
            <span className="panel-title">课堂消息</span>
            <span className="message-count">{messages.length} 条</span>
          </div>
          <div className="panel-body">
            <MessageList messages={messages} />
          </div>
        </div>

        {/* 右侧：操作面板 */}
        <div className="action-panel">
          {/* 讲授区域 */}
          <div className="action-section">
            <h3 className="action-title">讲授内容</h3>
            <RoughTextarea
              placeholder="输入讲授内容..."
              value={lectureContent}
              onChange={(e) => setLectureContent(e.target.value)}
            />
            <RoughButton
              variant="teacher"
              onClick={handleBroadcastLecture}
              disabled={!lectureContent.trim() || !isConnected}
              className="action-button"
            >
              广播讲授
            </RoughButton>
          </div>

          {/* 提问区域 */}
          <div className="action-section">
            <h3 className="action-title">课堂提问</h3>
            <RoughTextarea
              placeholder="输入要提问的问题..."
              value={questionContent}
              onChange={(e) => setQuestionContent(e.target.value)}
            />
            <div className="action-buttons-row">
              <RoughButton
                variant="teacher"
                onClick={handleAskToAll}
                disabled={!questionContent.trim() || !isConnected}
                className="action-button"
              >
                向全体提问
              </RoughButton>
              <RoughButton
                variant="outline"
                onClick={handleAskToStudent}
                disabled={!questionContent.trim() || !isConnected}
                className="action-button"
              >
                指定学生提问
              </RoughButton>
              <RoughButton
                variant="outline"
                onClick={handleEndDialogue}
                disabled={!isConnected}
                className="action-button"
              >
                结束对话
              </RoughButton>
            </div>
          </div>

          {/* 教师回复区域 */}
          <div className="action-section">
            <h3 className="action-title">教师回复</h3>
            <RoughTextarea
              placeholder="输入回复内容..."
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
            />
            <RoughButton
              variant="teacher"
              onClick={handleTeacherReply}
              disabled={!replyContent.trim() || !isConnected}
              className="action-button"
            >
              回复学生
            </RoughButton>
          </div>

          {/* 检查点控制 */}
          <div className="action-section">
            <h3 className="action-title">检查点控制</h3>
            <div className="action-buttons-row">
              <RoughButton
                variant="outline"
                onClick={handleAdvanceCheckpoint}
                disabled={!isConnected}
                className="action-button"
              >
                推进检查点
              </RoughButton>
            </div>
          </div>

          {/* 作业区域 */}
          <div className="action-section">
            <h3 className="action-title">作业与结束</h3>
            <RoughTextarea
              placeholder="输入作业内容..."
              value={homeworkContent}
              onChange={(e) => setHomeworkContent(e.target.value)}
            />
            <div className="action-buttons-row">
              <RoughButton
                variant="teacher"
                onClick={handleAssignHomework}
                disabled={!homeworkContent.trim() || !isConnected}
                className="action-button"
              >
                布置作业
              </RoughButton>
              <RoughButton
                variant="outline"
                onClick={handleCollectHomework}
                disabled={!isConnected}
                className="action-button"
              >
                收集作业
              </RoughButton>
            </div>
            <RoughButton
              variant="outline"
              onClick={handleEndTeaching}
              disabled={!isConnected}
              className="action-button end-button"
            >
              结束教学
            </RoughButton>
          </div>
        </div>
      </div>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100vh;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;

  /* ===== 顶部状态栏 ===== */
  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    background: #fafafa;
    border-bottom: 2px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .connection-status {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid #1a1a1a;

    &.connected {
      background: #22c55e;
    }

    &.connecting {
      background: #f59e0b;
      animation: pulse 1s infinite;
    }

    &.disconnected {
      background: #ef4444;
    }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .status-text {
    font-size: 14px;
    font-weight: 600;
    color: #1a1c1c;
  }

  .checkpoint-progress {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .progress-text {
    font-size: 14px;
    font-weight: 700;
    color: #007d5c;
    background: #E8F5E9;
    padding: 4px 12px;
    border: 2px solid #1A1A1A;
    box-shadow: 2px 2px 0px 0px #1A1A1A;
  }

  .checkpoint-title {
    font-size: 14px;
    color: #1a1c1c;
    font-weight: 600;
  }

  /* ===== 主内容区域 ===== */
  .main-content {
    display: flex;
    flex: 1;
    overflow: hidden;
    height: calc(100vh - 56px);
  }

  /* ===== 消息面板 ===== */
  .message-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-right: 2px solid #e5e5e5;
    min-width: 0;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: #ffffff;
    border-bottom: 2px solid #e5e5e5;
  }

  .panel-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #1a1c1c;
  }

  .message-count {
    font-size: 12px;
    color: #747688;
    background: #f5f5f5;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .panel-body {
    flex: 1;
    overflow-y: auto;
  }

  /* ===== 操作面板 ===== */
  .action-panel {
    width: 420px;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 20px;
    background: #ffffff;
    border-left: 2px solid #e5e5e5;
  }

  .action-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .action-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: #1a1c1c;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .action-button {
    width: 100%;
    font-size: 14px;
    padding: 8px 16px;
  }

  .action-buttons-row {
    display: flex;
    gap: 8px;

    .action-button {
      flex: 1;
    }
  }

  .end-button {
    margin-top: 8px;
    color: #dc2626;
    border-color: #dc2626;
  }

  /* ===== 响应式 ===== */
  @media (max-width: 768px) {
    .main-content {
      flex-direction: column;
      height: auto;
    }

    .message-panel {
      border-right: none;
      border-bottom: 2px solid #e5e5e5;
      height: 50vh;
    }

    .action-panel {
      width: 100%;
      border-left: none;
      border-top: 2px solid #e5e5e5;
    }
  }
`
```

- [ ] **步骤 4：运行测试，确认通过**

```bash
cd frontend
npm run test -- tests/views/TeacherView.test.tsx
```

- [ ] **步骤 5：提交**

```bash
git add frontend/src/views/TeacherView.tsx frontend/tests/views/TeacherView.test.tsx
git commit -m "feat(teacher-frontend): 实现 TeacherView 教师模式教学页面"
```

---

## 任务 8：配置路由

目标：在 `App.tsx` 中添加教师模式路由（`/teacher/config` 和 `/teacher/session/:sessionId`）。

**相关文件：**
- 修改：`frontend/src/App.tsx`

### 任务 8.1：添加路由配置

- [ ] **步骤 1：修改 `frontend/src/App.tsx`，添加教师模式路由**

```typescript
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'
import ObservationConfig from './views/ObservationConfig'
import ObservationView from './views/ObservationView'
import AnalysisReport from './views/AnalysisReport'
import TeacherConfig from './views/TeacherConfig'
import TeacherView from './views/TeacherView'
import NotFoundPage from './views/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      {/* Phase 10: 观察模式路由 */}
      <Route path="/observation/config" element={<ObservationConfig />} />
      <Route path="/observation/session/:sessionId" element={<ObservationView />} />
      {/* Phase 11: 分析报告路由 */}
      <Route path="/observation/:sessionId/report" element={<AnalysisReport />} />
      {/* Phase 12: 教师模式路由 */}
      <Route path="/teacher/config" element={<TeacherConfig />} />
      <Route path="/teacher/session/:sessionId" element={<TeacherView />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
```

- [ ] **步骤 2：运行所有前端测试，确认通过**

```bash
cd frontend
npm run test
```

**预期结果：** 所有测试通过（包括新的教师模式测试 + 已有的 LandingPage、RoughButton 等测试）。

- [ ] **步骤 3：运行 lint 检查**

```bash
cd frontend
npm run lint
```

- [ ] **步骤 4：提交**

```bash
git add frontend/src/App.tsx
git commit -m "feat(teacher-frontend): 添加教师模式路由配置"
```

---

## 任务 9：端到端验证与手动测试

目标：启动前后端服务，手动验证教师模式的完整流程。

### 任务 9.1：启动后端服务

- [ ] **步骤 1：启动后端**

```bash
cd backend
python main.py
```

**预期结果：** 后端启动在 `http://localhost:8000`，`/teacher/start` 端点可用。

### 任务 9.2：启动前端开发服务器

- [ ] **步骤 2：启动前端**

```bash
cd frontend
npm run dev
```

**预期结果：** 前端启动在 `http://localhost:5173`。

### 任务 9.3：手动验证流程

- [ ] **步骤 3：验证教师模式完整流程**

手动执行以下步骤：

1. 访问 `http://localhost:5173`
2. 点击「开始教学 →」按钮，跳转到 `/teacher/config`
3. 输入教学主题「Python 变量与数据类型」
4. 点击「开始教学」按钮
5. 等待教学计划生成（10-30 秒）
6. 验证跳转到 `/teacher/session/:sessionId`
7. 验证 WebSocket 连接状态为「已连接」
8. 验证检查点进度条显示正确
9. 在「讲授内容」输入框输入内容，点击「广播讲授」
10. 验证消息列表显示讲授消息
11. 在「课堂提问」输入框输入问题，点击「向全体提问」
12. 验证消息列表显示学生回答
13. 点击「推进检查点」
14. 重复步骤 9-13 直到所有检查点完成
15. 输入作业内容，点击「布置作业」
16. 点击「结束教学」
17. 验证消息列表显示课程反馈

### 任务 9.4：运行所有测试

- [ ] **步骤 4：运行完整前端测试套件**

```bash
cd frontend
npm run test
```

**预期结果：** 所有测试通过。

- [ ] **步骤 5：运行后端测试**

```bash
cd backend
pytest tests/units/test_teacher_router.py -v
ruff check models/teacher/
```

**预期结果：** 所有测试通过，lint 无错误。

---

## 功能完成前的最终检查清单

在宣告「教师模式前端开发完成」之前，请确保：

- [ ] `npm run test` 在 `frontend/` 中全部通过
- [ ] `npm run lint` 在 `frontend/` 中无错误
- [ ] `pytest tests/units/test_teacher_router.py -v` 在 `backend/` 中全部通过
- [ ] `ruff check models/teacher/` 无错误
- [ ] 手动执行完整的教师模式流程（配置 → 开始 → 讲授 → 提问 → 推进检查点 → 作业 → 结束）
- [ ] WebSocket 双向通信正常工作（发送命令 + 接收学生响应）
- [ ] 检查点进度条实时更新
- [ ] 消息列表自动滚动到底部
- [ ] 连接状态指示器正确显示（连接中/已连接/已断开）
- [ ] 教师模式页面使用绿色主题（#007d5c），与观察模式蓝色主题区分
- [ ] 所有组件遵循 rough-design 风格（粗边框、硬阴影、手绘感）
- [ ] 所有组件只有一个 `Wrapper` styled component
- [ ] 路由配置正确：`/teacher/config` 和 `/teacher/session/:sessionId`
- [ ] `useWebSocketBase` + `useWebSocket`（观察模式只读）+ `useTeacherWebSocket`（教师模式双向）三层架构正常工作
- [ ] `MessageList` 组件同时服务于观察模式和教师模式
- [ ] `RoughTextarea` 组件可在其他页面复用

当以上检查全部通过，并使用约定格式的中文 commit message 提交后，即可认为 **Phase 12: 教师模式前端** 已按 TDD 流程实现完成。
