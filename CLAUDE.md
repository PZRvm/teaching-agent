# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A teaching AI agent system (教学智能体) for educational scenarios with two primary modes:
1. **Teacher mode**: User acts as teacher controlling multiple student AI agents
2. **Observation mode**: User watches teacher and student agents interact automatically for educational research

The system supports three teaching modes:
- **灌输式** (Didactic): Lecture-based with minimal interaction
- **启发式** (Heuristic): Lecture with periodic checkpoint questions
- **讨论式** (Discussion): Frequent questions and guided discussion

## Architecture

### Backend Architecture

The backend follows a modular structure organized by feature:

**Backend Directory Structure:**
```
backend/
├── models/              # Feature modules (router + service + schemas)
│   ├── session/        # Teaching session management
│   │   ├── orchestrator.py     # SessionOrchestrator (观察模式核心)
│   │   ├── router_websocket.py # WebSocket endpoint (ws/{session_id})
│   │   └── schemas.py          # Message schemas (moved from schemas/)
│   ├── checkpoint/      # Checkpoint system (检查点系统)
│   │   ├── service.py          # CheckpointPlan generation service
│   │   ├── persistence_service.py # Checkpoint persistence (checkpoint_plans table)
│   │   ├── router.py           # GET/POST/PUT/DELETE /checkpoint-plans/
│   │   └── schemas.py          # Checkpoint, CheckpointPlan, CheckpointState
│   ├── observation/      # Observation mode (观察模式)
│   │   ├── router.py           # POST /observation/start, GET /observation/{id}/report
│   │   └── schemas.py          # ObservationConfig, ObservationStartResponse
│   └── user/           # User-related endpoints
├── agents/             # AI agent implementations
│   ├── memories/       # Agent memory dataclasses (按业务拆分)
│   │   ├── session_memory.py      # SessionMemory - 消息历史、摘要管理
│   │   ├── teacher_memory.py      # TeacherAgentMemory - 主题、参与度追踪
│   │   ├── student_memory.py      # StudentAgentMemory - 学习模拟
│   │   ├── memory_manager.py      # MemoryManager - 记忆编排器
│   │   └── memory_persistence.py  # MemoryPersistence - 数据库持久化
│   ├── tools/          # LangChain tools for agents
│   ├── teacher_agent.py
│   └── student_agent.py
├── core/               # Core business logic
│   ├── name_pool.py    # Chinese name pool for student generation
│   └── student_factory.py  # Student creation (manual/random/json)
├── configs/            # YAML configuration (no hardcoded values)
│   ├── llm.yml         # LLM model settings
│   ├── app.yml         # Application config (host, port, CORS)
│   └── database.yml    # Database (SQLite in datas/ directory)
├── datas/              # Data files (database.db, chroma/ vector store)
├── dependencies/       # Dependency injection
├── middlewares/        # Custom FastAPI middleware
├── schemas/            # Pydantic models for API validation (legacy - use models/*/schemas.py)
└── tests/              # Unit and integration tests
```

**Key Design Patterns:**

1. **Modular Router Structure**: Each feature (user, session) has its own directory with `router.py`, `service.py`, and related schemas. Import as `from models.{feature}.router import {router}`.

2. **YAML Configuration**: All configuration is in `configs/` directory. Access via:
   ```python
   from configs.config import settings
   api_key = settings.llm_api_key
   model = settings.llm_model
   ```

3. **Agent Memory System**: 按业务域拆分的模块化记忆管理（`agents/memories/`）
   - `session_memory.py` - **SessionMemory**: 会话级记忆，管理消息历史、教学摘要
   - `teacher_memory.py` - **TeacherAgentMemory**: 教师 agent 专用记忆
   - `student_memory.py` - **StudentAgentMemory**: 学生 agent 专用记忆（持久化到数据库）
   - `memory_manager.py` - **MemoryManager**: 记忆编排器，处理消息并更新各模块
   - `memory_persistence.py` - **MemoryPersistence**: 数据库持久化服务

4. **Checkpoint System**: 检查点驱动的教学流程（`models/checkpoint/`）
   - `CheckpointPlan`: 包含多个检查点的教学计划
   - `CheckpointState`: PENDING → TEACHING → QUESTIONS → COMPLETE
   - 灌输式跳过 QUESTIONS 状态
   - 三层降级机制（LLM 生成失败时的兜底策略）

5. **SessionOrchestrator**: 观察模式核心控制器（`models/session/orchestrator.py`）
   - 自动运行基于检查点的教学流程
   - 支持场景 A（教师提问）和场景 B（学生提问）对话循环
   - 至少一轮对话约束（双方均可结束）
   - 旁听学习机制（未参与对话的学生概率性学习）
   - WebSocket 实时推送检查点状态变更

6. **Message Schemas**: 消息类型和验证（`models/session/schemas.py`）
   - `Message`: sender, receiver, message_type, content, timestamp
   - `MessageType`: LECTURE, CHECKPOINT_QUESTION, ANSWER_TO_CHECKPOINT, ASK_QUESTION, REPLY_TO_STUDENT, ASSIGN_HOMEWORK, HOMEWORK_SUBMISSION, HOMEWORK_FEEDBACK, END_FEEDBACK

7. **StudentFactory Pattern**: Three modes for student creation:
   - Manual: Individual student configuration
   - Random: Generate entire class with distribution parameters
   - JSON import: Export/import for experiment reproducibility

**导入约定**:
```python
# 记忆系统（推荐从统一模块导入）
from agents.memories import SessionMemory, TeacherAgentMemory, StudentAgentMemory, MemoryManager, MemoryPersistence

# 检查点系统
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from models.checkpoint.service import CheckpointPlanService
from models.checkpoint.persistence_service import CheckpointPlanPersistence

# Session 系统
from models.session.orchestrator import SessionOrchestrator
from models.session.schemas import Message, MessageType

# Message schemas（向后兼容导入）
from schemas import Message, MessageType  # 从 models/session/schemas 重新导出
```

4. **StudentFactory Pattern**: Three modes for student creation:
   - Manual: Individual student configuration
   - Random: Generate entire class with distribution parameters
   - JSON import: Export/import for experiment reproducibility

### Frontend Architecture

**Frontend Directory Structure:**
```
frontend/
├── src/
│   ├── apis/          # API client functions (backend/ endpoints)
│   ├── components/    # React components (one Wrapper styled component per file)
│   ├── assets/        # Static resources
│   ├── App.tsx        # Root component
│   └── main.tsx       # Entry point
```

## Development Commands

### Frontend
```bash
cd frontend
npm run dev      # Start dev server (http://localhost:5173)
npm run build    # Build for production
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

### Backend
```bash
cd backend
python main.py       # Start dev server (http://0.0.0.0:8000)
ruff check .         # Check code issues
ruff check . --fix   # Auto-fix issues
ruff format .        # Format code
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Linting
- Frontend: `npm run lint` in [frontend/](frontend/)
- Backend: `ruff check .` in [backend/](backend/)
- ESLint config: [frontend/eslint.config.js](frontend/eslint.config.js)
- Ruff config: [backend/pyproject.toml](backend/pyproject.toml)
- TypeScript strict mode enabled with no-unused-locals and no-unused-parameters

### Testing

**Backend tests (pytest)**:
```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_memory_manager.py -v

# Run specific test class
pytest tests/test_memory_manager.py::TestSessionMemory -v

# Run specific test
pytest tests/test_memory_manager.py::TestSessionMemory::test_init_default_values -v

# Run tests by keyword
pytest tests/ -k "student_memory" -v

# Show print statements
pytest tests/ -v -s
```

**Frontend tests (vitest)**:
```bash
cd frontend

# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch
```

**Backend tests (pytest)**:
```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_memory_manager.py -v

# Run specific test class
pytest tests/test_memory_manager.py::TestSessionMemory -v

# Run specific test
pytest tests/test_memory_manager.py::TestSessionMemory::test_init_default_values -v

# Run tests by keyword
pytest tests/ -k "student_memory" -v

# Show print statements
pytest tests/ -v -s

# Run only unit tests (no LLM, no network)
pytest tests/units/ -v

# Run only integration tests (no LLM, may touch database/websocket)
pytest tests/integration/ -v

# Run unit tests that depend on mock LLM
pytest tests/unit_llm/ -v

# Run integration tests that call real LLM
pytest tests/integration_llm/ -v -s

# Run tests with coverage
pytest tests/ --cov=agents --cov=models --cov-report=html
```

**Test Organization**:
```
backend/tests/
├── units/              # 纯单元测试（无需 LLM、无需网络）
│   ├── test_memory_manager.py
│   ├── test_checkpoint_*.py
│   └── test_teacher_controller.py
├── integration/        # 纯后端集成测试（数据库、WebSocket 等，但不直接调用真实 LLM）
│   ├── test_session_orchestrator_full.py
│   └── test_teacher_controller_real.py
├── unit_llm/           # 带 LLM 的单元测试（使用 mock LLM，完全离线、可快速运行）
│   └── test_xxx_llm_*.py
├── integration_llm/    # 带真实 LLM 的集成测试（需要网络和 API Key，运行代价高）
│   └── test_xxx_llm_*.py
└── conftest.py         # Shared fixtures (test_engine, db_session, load .env)
```

**Test Fixtures**:
- `test_engine` - In-memory SQLite engine with all tables created
- `db_session` - Async database session for testing
- Async tests require `@pytest.mark.asyncio` decorator or class marked `@pytest.mark.asyncio`
- Environment variables loaded from `.env` via `load_dotenv()` in `conftest.py`

## Environment

- Backend runs on port 8000 (uvicorn)
- Frontend dev server runs on port 5173 (Vite default)
- Python 3.12+ required
- SQLite database in `backend/datas/database.db`
- Environment variables in `backend/.env` (use `.env.example` as template)

## Database Migrations (Alembic)

**Initialize migrations** (first time setup):
```bash
cd backend
alembic upgrade head
```

**Create new migration** (after modifying ORM models):
```bash
cd backend
alembic revision --autogenerate -m "描述变更内容"
```

**Apply migrations**:
```bash
cd backend
alembic upgrade head
```

**Rollback migration**:
```bash
cd backend
alembic downgrade -1
```

**Check migration status**:
```bash
cd backend
alembic current        # Current version
alembic history        # Migration history
```

**Database location**: `backend/datas/database.db`

## Current Development Progress

**Phase 1: 基础设施与数据层** ✅ 完成
- ORM models: TeachingSessionModel, SessionMemoryModel, TeacherMemoryModel, MessageModel
- Alembic migrations: 001_create_tables.py
- Pydantic schemas: TeachingSession, StudentProfile, Message

**Phase 2: 学生创建系统** ✅ 完成
- StudentFactory with three modes (manual/random/json)
- NamePool service (~100 Chinese names)
- RandomClassConfig with distribution support
- JSON import/export with validation

**Phase 3: Memory系统** ✅ 完成
- SessionMemory dataclass ([session_memory.py](backend/agents/memories/session_memory.py))
- TeacherAgentMemory dataclass ([teacher_memory.py](backend/agents/memories/teacher_memory.py))
- StudentAgentMemory dataclass ([student_memory.py](backend/agents/memories/student_memory.py))
- MemoryManager orchestrator ([memory_manager.py](backend/agents/memories/memory_manager.py))
- MemoryPersistence service ([memory_persistence.py](backend/agents/memories/memory_persistence.py))

**Phase 4: 教师Agent** ✅ 完成
- LangChain 基础集成（硅基流动 API + Qwen2.5-7B-Instruct）
- MemoryAwareTeacherAgent 基础结构
- 讲授、互动提问、回复学生、布置作业、评分、结束反馈功能

**Phase 5: 学生Agent** ✅ 完成
- LangChain 基础集成
- MemoryAwareStudentAgent 基础结构
- 回答问题、主动提问、做作业、课堂反馈功能
- 应答概率逻辑（should_respond）

**Phase 6: 对话系统** ✅ 完成
- 场景 A: 教师提问互动（checkpoint_question → answer_question → reply_to_student）
- 场景 B: 学生主动提问（ask_question → reply_to_student）
- 至少一轮对话约束（双方均可结束）
- 旁听学习机制（未参与对话的学生概率性学习）

**Phase 6.5: 检查点系统** ✅ 完成
- Checkpoint, CheckpointPlan, CheckpointState schemas
- CheckpointPlanService (LLM 生成，三层降级)
- CheckpointPlanPersistence (checkpoint_plans 独立表)
- API 端点: GET/POST/PUT/DELETE /checkpoint-plans/
- 测试覆盖: 75 个测试通过（17 单元测试 + 6 集成测试）

**Phase 7: SessionOrchestrator（观察模式核心）** ✅ 完成
- 基于检查点的自动教学流程编排
- 场景 A/B 对话循环（至少一轮约束）
- 旁听学习触发（检查点完成后）
- WebSocket 实时推送检查点状态变更
- 作业和反馈流程
- 测试覆盖: 245 个测试通过（241 单元测试 + 4 集成测试）

**Phase 7.5: TeacherSessionController（教师模式核心）** 🚧 进行中
- 计划文档: [2026-04-06-teacher-controller.md](docs/superpowers/plans/2026-04-06-teacher-controller.md)
- 关键特性: 无 TeacherAgent（用户扮演教师），手动检查点推进，编辑检查点计划

**Phase 8-13**: 待开始

## Code Style Guide

### Frontend Components

All React components must follow this pattern:

```tsx
import styled from 'styled-components'

export default function MyComponent() {
  return (
    <Wrapper>
      <div className="header">标题</div>
      <div className="content">
        <p className="text">内容</p>
      </div>
    </Wrapper>
  )
}

// Only ONE Wrapper styled component
// Use nested class selectors for internal elements
const Wrapper = styled.div`
  padding: 20px;

  .header {
    font-size: 24px;
  }

  .content {
    padding: 10px;

    .text {
      font-size: 16px;
    }
  }
`
```

**Rules:**
- Use only ONE `Wrapper` styled component per file
- Internal elements use regular HTML with `className` (kebab-case)
- Define nested class styles inside `Wrapper`
- Support multi-level nesting with `&`

**Naming:**
- Component files: PascalCase (`UserProfile.tsx`)
- Wrapper: Always named `Wrapper`
- Classes: kebab-case (`header`, `content`, `user-name`)

### Python Code Style

Follow PEP 8 with these additional rules:

```python
from fastapi import APIRouter
from typing import List

router = APIRouter()


@router.get("/users/", summary="获取用户列表")
async def read_users() -> List[dict]:
    """
    获取所有用户列表

    Returns:
        List[dict]: 用户列表
    """
    return [{"username": "Rick"}, {"username": "Morty"}]
```

**Rules:**
- Use type hints for all function parameters and returns
- Add docstrings for all functions and classes
- Use `async def` for async operations
- Order imports: stdlib → third-party → local
- Max line length: 100 characters

**Naming:**
- Files and modules: `snake_case`
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

### File Organization

**按业务域拆分文件**:
- 当一个文件包含多个不相关的类或超过200行时，应按业务域拆分
- 每个文件应只负责一个明确的业务领域
- 拆分后使用统一的 `__init__.py` 或导出模块保持导入简洁

**示例 - agents/memories/ 模块**:
```
agents/memories/
├── __init__.py              # 统一导出所有公开类
├── session_memory.py        # SessionMemory 类（会话级记忆）
├── teacher_memory.py        # TeacherAgentMemory 类（教师记忆）
├── student_memory.py        # StudentAgentMemory 类（学生记忆）
└── memory_manager.py        # MemoryManager 类（编排器，未来实现）
```

**导入约定**:
```python
# 推荐：从业务模块直接导入
from agents.memories import SessionMemory, TeacherAgentMemory

# 或：从具体文件导入（如果只需要单个类）
from agents.memories.session_memory import SessionMemory
```

## Documentation Requirements

**Code-Documentation Sync**: All code changes must be accompanied by corresponding documentation updates. This ensures documentation stays in sync with implementation.

### API Changes

When modifying API endpoints (adding, changing, or removing routes), update `docs/api.md` with:

- Endpoint path and HTTP method
- Query parameters, path parameters, and request body schemas
- Response examples with actual data
- Error cases and status codes
- Data model changes and field descriptions

**Example**: After adding a new endpoint like `POST /checkpoint-plans/`, document it with:
```markdown
### 创建检查点计划

创建一个新的教学检查点计划。

```http
POST /checkpoint-plans/
```

**Query 参数:**
- `session_id` (integer, required) - 教学会话 ID

**请求体:**
```json
{
  "topic": "Python 变量与数据类型",
  "teaching_mode": "didactic",
  "checkpoints": [...]
}
```

**响应示例:**
```json
{
  "plan_id": 1
}
```
```

### Test Changes

When adding or modifying tests, update `docs/tests/backend/index.md` with:

- Test file path (relative to `backend/tests/`)
- Test class names with descriptions
- Test method names with descriptions of what they test
- Running commands for specific tests

**Example**: After adding tests for checkpoint system, document them as:
```markdown
### tests/units/test_checkpoint_persistence.py
Checkpoint persistence service 单元测试

- **TestCheckpointPlanPersistence** - CheckpointPlanPersistence 测试类
  - `test_save_plan()` - 测试保存检查点计划到数据库
  - `test_load_plan()` - 测试从数据库加载检查点计划
  - `test_update_checkpoint_state()` - 测试更新检查点状态
  - `test_advance_checkpoint()` - 测试推进到下一个检查点
```

### Documentation Update Checklist

Before committing code changes, verify:

- [ ] If API changed: `docs/api.md` updated with new/modified endpoints
- [ ] If tests added/modified: `docs/tests/backend/index.md` updated with test documentation
- [ ] Documentation examples are accurate and runnable
- [ ] Error cases are documented with correct status codes

## Development Planning Workflow

The project uses **TDD (Test-Driven Development)** as the mandatory development methodology for all features. All implementation plans follow the TDD cycle and are stored in `docs/superpowers/plans/`:

**Plan Format**: `YYYY-MM-DD-<feature-name>.md`

**Example Plans**:
- `2026-04-05-session-orchestrator.md` - Phase 7: SessionOrchestrator implementation
- `2026-04-06-teacher-controller.md` - Phase 7.5: TeacherSessionController implementation

**Plan Structure**:
1. File structure mapping (which files to create/modify)
2. Bite-sized TDD tasks (RED-GREEN-REFACTOR cycle per task)
3. Complete code examples for each step
4. Verification commands and acceptance criteria

### TDD Cycle (Mandatory)

Every task must follow the **RED-GREEN-REFACTOR-COMMIT** cycle:

```
┌─────────────────────────────────────────────────────────────┐
│  1. RED (Write failing test)                                │
│     - Write test code first                                 │
│     - Run pytest to verify it fails                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. GREEN (Make test pass)                                  │
│     - Write minimal implementation                          │
│     - Run pytest to verify it passes                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. REFACTOR (Improve code)                                 │
│     - Refactor while keeping tests green                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. COMMIT (Save progress)                                  │
│     - Commit with conventional commit message               │
└─────────────────────────────────────────────────────────────┘
```

**TDD Commands**:
```bash
# RED: Verify test fails
pytest tests/units/test_feature.py::test_specific_case -v

# GREEN: Verify test passes
pytest tests/units/test_feature.py::test_specific_case -v

# Run all tests for the feature
pytest tests/units/test_feature.py -v

# Code quality check
ruff check models/feature/
ruff format models/feature/
```

### Plan Creation and Execution

**Creating a New Plan**: Use the `superpowers:writing-plans` skill with the spec/design documents to generate comprehensive TDD plans before touching code.

**Executing a Plan**: **Use `superpowers:test-driven-development` skill to implement task-by-task following the TDD cycle.** This is the required skill for all implementation work.

### TDD Best Practices

1. **Test Naming**: Use descriptive names: `test_<method>_<scenario>_<expected_result>()`
   - Example: `test_handle_broadcast_lecture_records_to_memory()`

2. **Mock External Dependencies**: Unit tests use Mock for LLM, database, etc.
   - Integration tests use real dependencies for end-to-end validation

3. **Commit Messages**: Follow conventional commit format，并且**提交描述部分必须使用中文**
   - Format: `<type>(<scope>): <description>`
   - Types: `feat`, `fix`, `refactor`, `test`, `chore`
   - Example: `feat(teacher-controller): 新增 handle_broadcast_lecture 方法`

4. **Error Path Testing**: Every method must test both happy path and error paths
   - Don't just test that it works—test that it fails correctly too

5. **Python Test Data**: Use Python-related knowledge for test content
   - Topics: Python variables, data types, functions, classes, etc.
   - Avoid: Math formulas or domain-specific knowledge

## Important Architecture Decisions

### Two Teaching Modes

**观察模式 (Observation Mode)**: User watches teacher and student agents interact automatically
- **Controller**: `SessionOrchestrator` (自动运行基于检查点的教学流程)
- **Teacher Agent**: AI 教师自动讲授、提问、回复
- **Checkpoint Progression**: 自动推进到下一个检查点
- **Use Case**: Educational research, studying AI teaching patterns

**教师模式 (Teacher Mode)**: User acts as teacher controlling multiple student AI agents
- **Controller**: `TeacherSessionController` (用户手动控制教学流程)
- **Teacher Agent**: 无（用户扮演教师角色）
- **Checkpoint Progression**: 手动推进（用户决定何时推进）
- **Use Case**: Interactive teaching, teacher training, human-in-the-loop

**Common Features**:
- 基于检查点的教学结构（`CheckpointPlan`）
- 至少一轮对话约束（双方均可结束）
- 旁听学习机制（未参与对话的学生概率性学习）
- WebSocket 实时推送状态变更

### Checkpoint System

**Checkpoint State Machine**: PENDING → TEACHING → QUESTIONS → COMPLETE
- **Didactic (灌输式)**: 跳过 QUESTIONS 状态
- **Heuristic (启发式)**: 每个检查点讲授后提问一次
- **Discussion (讨论式)**: 每个检查点讲授后引导讨论
- **Teacher (教师模式)**: 用户手动控制，系统仅提供结构

**Three-Layer Fallback**: LLM 生成检查点计划失败时的降级策略
- Layer 1: Full LLM generation (详细检查点)
- Layer 2: Simplified LLM generation (3 检查点)
- Layer 3: Single checkpoint fallback (1 检查点兜底)

### Message Flow Patterns

**场景 A: 教师提问互动**
```
teacher: checkpoint_question → student: answer_question → teacher: reply_to_student
(循环: 至少一轮后双方均可结束)
```

**场景 B: 学生主动提问**
```
student: ask_question → teacher: reply_to_student
(循环: 至少一轮后双方均可结束)
```

**旁听学习**: 对话结束后，未参与对话的学生基于 `attitude`/`learning_ability` 概率性调用 `update_knowledge()`

### Database Architecture

1. **No Knowledge Base System (v1)**: The system uses LLM's native capabilities for teaching. Knowledge base (ChromaDB, RAG) was removed from v1 scope. Future enhancement may add structured course content.

2. **Models/ over Routers/**: Backend uses `models/` directory with feature-based organization instead of flat `routers/`. Each feature module contains its own router, service, and related logic.

3. **Database in datas/**: All data files (SQLite database, ChromaDB vector store) go in `backend/datas/` directory for centralized management and easier cleanup.

4. **checkpoint_plans 独立表**: 检查点计划使用 JSON 字段存储完整的 `CheckpointPlan` 对象，支持快速读写和状态更新。

5. **LLM Evaluation of Homework**: Students' homework is evaluated by LLM, not keyword matching. This allows for more nuanced feedback.

6. **Teacher Can Reject Student Questions**: In reply_to_teacher message type, teachers may choose not to respond to certain student questions based on teaching context.

### WebSocket Protocol

**Backend → Frontend Events**:
```json
{
  "type": "checkpoint_state_change",
  "data": {
    "index": 2,
    "checkpoint": {"title": "...", "state": "teaching", "key_point": "..."},
    "progress": {"current": 2, "total": 5, "completed": 1}
  }
}
```

**Frontend → Backend Commands (教师模式)**:
- `broadcast_lecture`: 用户广播讲授内容
- `ask_to_all`: 向全体提问并收集回答
- `ask_to_student`: 向指定学生提问
- `teacher_reply`: 教师回复（对话循环）
- `end_dialogue`: 结束对话（触发旁听学习）
- `advance_checkpoint`: 手动推进检查点（可强制结束当前对话）

## Known Issues and Workarounds

### API Rate Limiting (Integration Tests)

**Issue**: 4 integration tests fail with `HTTP/1.1 429 Too Many Requests` when running integration tests concurrently. This is caused by the SiliconFlow API rate limiting during concurrent LLM calls.

**Workaround**: Run integration tests serially or use mock LLM for testing:
```bash
# Run integration tests serially (slower but avoids rate limiting)
pytest tests/integration/ -v --tb=short

# Skip integration tests if only unit tests needed
pytest tests/units/ -v
```

**Note**: Unit tests cover all core logic and pass consistently (241 unit tests). Integration test failures are due to external API infrastructure, not code bugs.
