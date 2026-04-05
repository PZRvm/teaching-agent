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
│   ├── user/           # User-related endpoints
│   └── session/        # Teaching session management
├── agents/             # AI agent implementations
│   ├── memories/       # Agent memory dataclasses (按业务拆分)
│   │   ├── session_memory.py      # SessionMemory - 消息历史、摘要管理
│   │   ├── teacher_memory.py      # TeacherAgentMemory - 主题、参与度追踪
│   │   ├── student_memory.py      # StudentAgentMemory - 学习模拟
│   │   └── memory_manager.py      # 统一导出模块（未来：MemoryManager编排）
│   ├── tools/          # LangChain tools for agents
│   ├── teacher_agent.py
│   └── student_agent.py
├── core/               # Core business logic
├── configs/            # YAML configuration (no hardcoded values)
│   ├── llm.yml         # LLM model settings
│   ├── app.yml         # Application config (host, port, CORS)
│   └── database.yml    # Database (SQLite in datas/ directory)
├── datas/              # Data files (database.db, chroma/ vector store)
├── dependencies/       # Dependency injection
├── middlewares/        # Custom FastAPI middleware
├── schemas/            # Pydantic models for API validation
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
     - `add_message()` - 添加消息到历史
     - `should_update_summary()` - 判断是否需要更新摘要（基于间隔）
     - `get_recent_messages()` - 获取最近 N 条消息（上下文窗口）
     - `get_agent_context()` - 生成 LLM 上下文字符串
   
   - `teacher_memory.py` - **TeacherAgentMemory**: 教师 agent 专用记忆
     - `record_covered_topic()` - 记录已讲授主题（去重）
     - `record_student_question()` - 记录学生提问
     - `record_student_participation()` - 记录学生参与次数
     - `record_misconception()` - 记录学生误解
     - `get_system_prompt_addition()` - 生成教师 system prompt
   
   - `student_memory.py` - **StudentAgentMemory**: 学生 agent 专用记忆（持久化到数据库）
     - `from_profile()` - 从 StudentProfile 创建实例
     - `should_remember_concept()` - 判断是否记住概念（基于学习参数）
     - `update_knowledge()` - 尝试学习新概念（概率性）
     - `get_system_prompt_addition()` - 生成学生 system prompt
   
   - `memory_manager.py` - 统一导出模块，未来将包含 MemoryManager 编排类
   
   **导入方式**:
   ```python
   # 推荐：从统一模块导入
   from agents.memories import SessionMemory, TeacherAgentMemory, StudentAgentMemory
   
   # 或：从具体模块导入
   from agents.memories.session_memory import SessionMemory
   from agents.memories.teacher_memory import TeacherAgentMemory
   from agents.memories.student_memory import StudentAgentMemory
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

**Test Fixtures**:
- `test_engine` - In-memory SQLite engine with all tables created
- `db_session` - Async database session for testing
- Async tests require `@pytest.mark.asyncio` or class marked `@pytest.mark.asyncio`

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

**Phase 3: Memory系统** 🚧 进行中 (Tasks 0-3 完成，6 任务剩余)
- ✅ SessionMemory dataclass ([session_memory.py](backend/agents/memories/session_memory.py))
- ✅ TeacherAgentMemory dataclass ([teacher_memory.py](backend/agents/memories/teacher_memory.py))
- ✅ StudentAgentMemory dataclass ([student_memory.py](backend/agents/memories/student_memory.py))
- ⏳ MemoryManager orchestrator (pending)
- ⏳ MemoryPersistence service (pending)
- ⏳ Integration tests (pending)

**Phase 4-13**: 待开始

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

## Important Architecture Decisions

1. **No Knowledge Base System (v1)**: The system uses LLM's native capabilities for teaching. Knowledge base (ChromaDB, RAG) was removed from v1 scope. Future enhancement may add structured course content.

2. **Models/ over Routers/**: Backend uses `models/` directory with feature-based organization instead of flat `routers/`. Each feature module contains its own router, service, and related logic.

3. **Database in datas/**: All data files (SQLite database, ChromaDB vector store) go in `backend/datas/` directory for centralized management and easier cleanup.

4. **LLM Evaluation of Homework**: Students' homework is evaluated by LLM, not keyword matching. This allows for more nuanced feedback.

5. **Teacher Can Reject Student Questions**: In reply_to_teacher message type, teachers may choose not to respond to certain student questions based on teaching context.
