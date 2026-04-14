# 后端自动化测试文档

本文档详细描述后端测试体系。

## 测试框架

| 框架/库 | 版本 | 用途 |
|---------|------|------|
| pytest | 8.0+ | 测试运行器 |
| pytest-asyncio | 0.24+ | 异步测试支持 |
| pytest-cov | 5.0+ | 代码覆盖率 |
| pytest-mock | 3.14+ | Mock 功能 |
| httpx | 0.27+ | FastAPI 异步测试客户端 |

## 测试文件结构

```
backend/tests/
├── __init__.py                # 测试模块初始化
├── conftest.py                # pytest 配置和 fixtures
├── units/                     # 单元测试
│   ├── test_checkpoint_*.py   # 检查点系统测试 (4 个文件)
│   ├── test_connection_manager.py   # ConnectionManager WebSocket 连接池测试
│   ├── test_llm_*.py         # LLM 相关测试 (2 个文件)
│   ├── test_memory_manager.py # MemoryManager 测试
│   ├── test_name_pool.py     # NamePool 服务测试
│   ├── test_orchestrator_ws_push.py # SessionOrchestrator WebSocket 推送测试
│   ├── test_schemas.py       # Pydantic schema 验证测试
│   ├── test_session_registry.py     # SessionRegistry 会话注册表测试
│   ├── test_ws_command_router.py    # WebSocket 命令 schema 和路由测试
│   ├── test_settings.py      # 配置加载测试
│   ├── test_student_*.py     # 学生相关测试 (2 个文件)
│   ├── test_teacher_agent.py # TeacherAgent 单元测试
│   ├── test_teacher_controller.py # TeacherSessionController 单元测试
│   └── test_teacher_controller_ws_push.py # TeacherController WebSocket 推送测试
├── integration/              # 集成测试
│   ├── test_alembic_migration.py    # Alembic 数据库迁移测试
│   ├── test_checkpoint_api.py       # Checkpoint API 集成测试
│   ├── test_checkpoint_service_real.py # 真实 LLM checkpoint 生成测试
│   ├── test_database.py             # 数据库集成测试
│   ├── test_memory_persistence.py   # 记忆持久化集成测试
│   ├── test_observation_api.py      # 观察模式 API 集成测试
│   ├── test_session_api.py          # 会话管理 API 集成测试
│   ├── test_student_memory_migration.py # 学生记忆迁移测试
│   ├── test_teacher_agent_real.py  # 教师 Agent 真实 LLM 测试
│   ├── test_teacher_controller_api.py # TeacherController REST API 集成测试
│   ├── test_teacher_controller_full_classroom.py # TeacherSessionController 全课堂流程集成测试
│   └── test_websocket.py            # WebSocket 端点集成测试
├── unit_llm/                 # 带 Mock LLM 的单元测试
│   ├── test_session_orchestrator.py # SessionOrchestrator 上下文隔离测试
│   └── test_teacher_agent.py       # TeacherAgent Mock LLM 测试
```

## 测试统计概览

| 分类 | 文件数 | 测试类数 | 测试方法数 |
|------|--------|---------|-----------|
| **单元测试** | 18 | 69 | 180+ |
| **Mock LLM 单元测试** | 2 | 3 | 6+ |
| **集成测试** | 11 | 20 | 56+ |
| **总计** | 31 | 92 | 242+ |

---

## Pytest Fixtures

项目定义了以下 fixtures（在 `tests/conftest.py`）：

> **注意**: `asyncio_mode = "auto"` 已在 `pyproject.toml` 中配置，无需手动添加 `@pytest.mark.asyncio` 装饰器。

### test_engine
- **作用**: 创建测试数据库引擎（内存 SQLite）
- **范围**: function
- **返回**: `(engine, Base)` 元组
- **用途**: 数据库表创建和清理

```python
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    from core.database import Base

    # Import all ORM models so they register with Base.metadata
    from orm.checkpoint_plan import CheckpointPlanModel  # noqa: F401
    from orm.message import MessageModel  # noqa: F401
    from orm.session_memory import SessionMemoryModel  # noqa: F401
    from orm.student_memory import StudentMemoryModel  # noqa: F401
    from orm.teacher_memory import TeacherMemoryModel  # noqa: F401
    from orm.teaching_session import TeachingSessionModel  # noqa: F401

    engine = create_async_engine(TEST_DATABASE_URL, ...)

    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine, Base

    # 清理表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### db_session
- **作用**: 创建数据库会话
- **范围**: function
- **返回**: `AsyncSession`
- **用途**: 数据库操作

```python
@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine, base = test_engine
    async_session_maker = async_sessionmaker(engine, ...)

    async with async_session_maker() as session:
        yield session
```

### test_engine_file
- **作用**: 创建测试数据库引擎（文件 SQLite，用于跨连接数据共享）
- **范围**: function
- **返回**: `(engine, Base, tmp_path, url)` 元组
- **用途**: ASGITransport 测试（HTTP 请求创建独立连接，需要文件数据库共享数据）

### db_session_file
- **作用**: 创建数据库会话（文件 SQLite）
- **范围**: function
- **返回**: `AsyncSession`
- **用途**: ASGITransport 集成测试

---

## test_database.py - 数据库 ORM 测试

测试所有 ORM 模型的 CRUD 操作。

### TestTeachingSessionModel (2 个测试)

#### `test_create_teaching_session`
**目的**: 验证可以创建教学会话并保存到数据库

**测试步骤**:
1. 创建 `TeachingSessionModel` 实例
2. 添加到数据库会话
3. 提交事务
4. 刷新对象获取生成的 ID
5. 验证字段值正确

```python
async def test_create_teaching_session(self, db_session: AsyncSession) -> None:
    session = TeachingSessionModel(
        teaching_mode="didactic",
        topic="Test Topic",
        students_config=[{"name": "Alice"}],
        duration_seconds=3600,
        status="running",
        start_time=datetime.utcnow(),
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    assert session.id is not None
    assert session.teaching_mode == "didactic"
    assert session.topic == "Test Topic"
    assert session.status == "running"
```

#### `test_read_teaching_session`
**目的**: 验证可以从数据库读取教学会话

**测试步骤**:
1. 创建并保存教学会话
2. 使用 `select` 查询数据库
3. 验证查询结果正确

### TestMessageModel (2 个测试)

#### `test_create_message`
**目的**: 验证可以创建消息并与教学会话关联

**测试步骤**:
1. 先创建教学会话（外键依赖）
2. 创建消息记录
3. 验证消息字段值正确

#### `test_message_session_relationship`
**目的**: 验证消息与会话的一对多关系

**测试步骤**:
1. 创建教学会话
2. 创建多条消息关联到同一会话
3. 查询该会话的所有消息
4. 验证返回 3 条消息

### TestSessionMemoryModel (1 个测试)

#### `test_create_session_memory`
**目的**: 验证会话记忆可以正确保存

**测试覆盖**:
- `message_history` JSON 字段
- `teaching_summary` 文本字段
- 外键关系验证

### TestTeacherMemoryModel (1 个测试)

#### `test_create_teacher_memory`
**目的**: 验证教师记忆可以正确保存

**测试覆盖**:
- `covered_topics` - 已讲授知识点
- `student_questions` - 学生问题追踪
- `student_participation` - 参与度统计
- `teaching_progress` - 教学进度 (0.0-1.0)
- `student_misconceptions` - 学生误解追踪

---

## test_schemas.py - Pydantic Schema 验证测试

测试所有 API 请求/响应模型的数据验证。

### TestStudentProfile (7 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_valid_student_profile` | 有效学生配置创建 |
| `test_name_too_short` | 名字少于 1 字符 |
| `test_name_too_long` | 名字超过 20 字符 |
| `test_name_whitespace_only` | 纯空白格名字 |
| `test_learning_ability_out_of_range_low` | 学习能力 < 1 |
| `test_learning_ability_out_of_range_high` | 学习能力 > 10 |
| `test_default_values` | 默认值（level=AVERAGE, attitude=NEUTRAL） |

**字段验证规则**:
```python
class StudentProfile(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    level: StudentLevel = Field(default=StudentLevel.AVERAGE)
    attitude: StudentAttitude = Field(default=StudentAttitude.NEUTRAL)
    learning_ability: int = Field(ge=1, le=10)
```

### TestRandomClassConfig (4 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_valid_random_config` | 有效随机班级配置 |
| `test_level_distribution_not_sum_to_one` | 分布比例不等于 1.0 |
| `test_total_students_too_small` | 学生数 < 2 |
| `test_total_students_too_large` | 学生数 > 50 |

**自定义验证器**:
```python
@field_validator("level_distribution", "attitude_distribution")
@classmethod
def distribution_sum_to_one(cls, v: dict) -> dict:
    if not (0.99 <= sum(v.values()) <= 1.01):
        raise ValueError("分布比例总和必须为1.0")
    return v
```

### TestTeachingSessionCreate (4 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_valid_session_create` | 有效教学会话创建 |
| `test_topic_too_long` | 主题超过 200 字符 |
| `test_duration_too_short` | 时长少于 60 秒 |
| `test_optional_duration` | duration_seconds 可选 |

### TestMessage (3 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_valid_message` | 有效消息创建 |
| `test_content_empty` | 消息内容为空 |
| `test_message_create_with_session_id` | 带会话 ID 的消息 |

---

## 运行后端测试

### 基本命令

```bash
# 进入后端目录
cd backend

# 运行所有测试
pytest

# 运行所有测试（详细输出）
pytest -v

# 运行特定测试文件
pytest tests/test_database.py

# 运行特定测试类
pytest tests/test_database.py::TestTeachingSessionModel

# 运行特定测试方法
pytest tests/test_database.py::TestTeachingSessionModel::test_create_teaching_session
```

### 覆盖率报告

```bash
# 生成终端覆盖率报告
pytest --cov=backend --cov-report=term-missing

# 生成 HTML 覆盖率报告（在 htmlcov/index.html 查看）
pytest --cov=backend --cov-report=html

# 生成 XML 覆盖率报告（用于 CI）
pytest --cov=backend --cov-report=xml
```

### 调试测试

```bash
# 详细输出（显示 print 内容）
pytest -vv -s

# 在第一个失败时进入 pdb 调试器
pytest --pdb

# 在失败时进入 pdb（包括捕获的异常）
pytest --pdb-trace

# 只运行上次失败的测试
pytest --lf

# 先运行失败的，再运行通过的
pytest --ff
```

### 并行测试（需要 pytest-xdist）

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用所有 CPU 核心并行运行
pytest -n auto

# 指定并行进程数
pytest -n 4
```

---

## 测试覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| ORM 模型 (`orm/`) | >80% | ✅ 达标 |
| Schemas (`schemas/`) | >90% | ✅ 达标 |
| 核心业务逻辑 (`core/`) | >70% | 🚧 待实现 |
| 服务层 (`services/`) | >60% | 🚧 待实现 |
| API 路由 (`models/`) | >60% | 🚧 待实现 |
| **总体** | **>60%** | **🚧 进行中** |

---

## 测试最佳实践

### 1. AAA 模式 (Arrange-Act-Assert)

```python
def test_student_name_validation():
    # Arrange - 准备测试数据
    invalid_name = ""

    # Act - 执行被测试的操作
    with pytest.raises(ValidationError):
        StudentProfile(name=invalid_name, learning_ability=5)

    # Assert - 验证结果
    # 异常被抛出即验证通过
```

### 2. 使用描述性测试名称

```python
# ✅ 好的测试名称
def test_create_teaching_session_with_valid_data():
    """测试：使用有效数据创建教学会话"""
    pass

# ❌ 避免的测试名称
def test1():
    pass
def test_create():
    pass
```

### 3. 测试隔离

每个测试应该独立运行，不依赖其他测试或执行顺序。

```python
# ✅ 好的做法 - 每个测试创建独立数据
@pytest.mark.asyncio
async def test_read_session(db_session: AsyncSession):
    # 创建自己的测试数据
    session = TeachingSessionModel(...)
    db_session.add(session)
    await db_session.commit()
    
    # 执行测试
    result = await db_session.execute(select(TeachingSessionModel))
    assert result.scalar_one_or_none() is not None

# ❌ 避免的做法 - 依赖全局状态或测试执行顺序
def test_something():
    global shared_state  # 不要使用全局状态
    shared_state = modify()
```

### 4. 异步测试规范

```python
# 必须使用 @pytest.mark.asyncio 装饰器
@pytest.mark.asyncio
async def test_async_operation():
    # 使用 async/await
    result = await some_async_function()
    assert result is not None
```

### 5. Fixture 复用

```python
# 定义可复用的 fixture
@pytest_asyncio.fixture
async def sample_session(db_session):
    session = TeachingSessionModel(
        teaching_mode="didactic",
        topic="Sample",
        students_config=[],
        start_time=datetime.utcnow(),
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session

# 在测试中使用
@pytest.mark.asyncio
async def test_use_fixture(sample_session):
    assert sample_session.id is not None
    assert sample_session.teaching_mode == "didactic"
```

---

## 常见问题

### Q: 测试失败 "no such table"？

**原因**: ORM 模型没有被导入，导致表未创建。

**解决**: 确保 `conftest.py` 中导入了所有 ORM 模型：
```python
# 导入所有 ORM 模型（即使显示未使用也要保留）
from orm.message import MessageModel  # noqa: F401
from orm.session_memory import SessionMemoryModel  # noqa: F401
from orm.teacher_memory import TeacherMemoryModel  # noqa: F401
from orm.teaching_session import TeachingSessionModel  # noqa: F401
```

### Q: 异步测试不执行？

**原因**: 缺少 `@pytest.mark.asyncio` 装饰器。

**解决**:
```python
@pytest.mark.asyncio  # 必须添加
async def test_async_function():
    result = await async_operation()
    assert result
```

### Q: pytest-asyncio 警告 "async def functions are not supported"？

**原因**: pytest-asyncio 配置问题。

**解决**: 在 `pyproject.toml` 中配置：
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

或使用 `@pytest_asyncio.fixture` 装饰 async fixtures：
```python
import pytest_asyncio

@pytest_asyncio.fixture
async def async_fixture():
    return await something()
```

### Q: 测试运行太慢？

**原因**: 每个测试都创建真实的数据库连接。

**解决方案**:
1. 使用内存数据库（已配置）
2. 并行运行测试：`pytest -n auto`
3. 跳过慢速测试：`pytest -m "not slow"`
4. 使用 mock 替代数据库操作

---

## 单元测试详解

### test_checkpoint_persistence_service.py - CheckpointPlanPersistence 单元测试

**测试类**: `TestCheckpointPlanPersistence` (6 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_save_plan_creates_new_record` | 保存新计划到数据库 |
| `test_load_plan_by_session_id` | 根据 session_id 加载计划 |
| `test_load_plan_returns_none_for_nonexistent_session` | 不存在的 session_id 返回 None |
| `test_update_checkpoint_state` | 更新检查点状态 |
| `test_advance_to_next_checkpoint` | 推进到下一个检查点 |
| `test_delete_plan_by_session_id` | 删除计划 |

**运行命令**:
```bash
pytest tests/units/test_checkpoint_persistence_service.py -v
```

### test_checkpoint_persistence.py - CheckpointPlan ORM 模型测试

**测试类**: `TestCheckpointPersistence` (4 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_create_checkpoint_plan` | 创建检查点计划并保存 |
| `test_load_checkpoint_plan` | 加载检查点计划 |
| `test_update_checkpoint_plan` | 更新检查点计划 |
| `test_delete_checkpoint_plan` | 删除检查点计划 |

### test_checkpoint_schemas.py - Checkpoint Schema 验证测试

**测试类**: 3 个测试类，17 个测试

#### TestCheckpointState (1 个测试)
- `test_checkpoint_state_values` - 验证所有状态值

#### TestCheckpoint (4 个测试)
- `test_valid_checkpoint` - 有效检查点创建
- `test_checkpoint_with_examples` - 带示例的检查点
- `test_checkpoint_state_default` - 默认状态为 PENDING
- `test_checkpoint_json_serialization` - JSON 序列化

#### TestCheckpointPlan (12 个测试)
- `test_valid_checkpoint_plan` - 有效检查点计划
- `test_empty_checkpoints` - 空检查点列表验证
- `test_invalid_teaching_mode` - 无效教学模式
- `test_json_serialization` - JSON 序列化
- `test_add_checkpoint` - 添加检查点
- `test_get_current_checkpoint` - 获取当前检查点
- `test_advance_checkpoint` - 推进检查点
- `test_advance_beyond_last` - 超出最后检查点
- `test_get_pending_checkpoints` - 获取待处理检查点
- `test_get_completed_checkpoints` - 获取已完成检查点
- `test_all_checkpoints_completed` - 所有检查点完成状态

### test_checkpoint_service.py - CheckpointPlanService 单元测试

**测试类**: `TestCheckpointPlanService` (8 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_generate_plan_with_structured_output` | 使用 structured output 生成 |
| `test_generate_plan_fallback_to_json_parsing` | 降级到 JSON 解析 |
| `test_generate_plan_fallback_to_single_checkpoint` | 降级到单检查点兜底 |
| `test_generate_plan_validates_teaching_mode` | 教学模式验证 |
| `test_build_prompt_includes_topic_and_mode` | prompt 包含主题和模式 |
| `test_load_mode_instructions` | 加载教学模式指令 |
| `test_parse_json_handles_markdown_code_blocks` | JSON 解析处理 Markdown |
| `test_parse_json_handles_plain_json` | JSON 解析处理纯 JSON |

### test_llm_client.py - LLMClient 单元测试

**测试类**: `TestLLMClient` (8 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_from_config_loads_yaml` | 从配置文件加载 |
| `test_from_config_requires_api_key` | API key 必需验证 |
| `test_invoke_returns_string` | invoke 返回字符串 |
| `test_invoke_with_temperature_override` | 温度参数覆盖 |
| `test_invoke_with_messages` | 消息列表调用 |
| `test_stream_yields_chunks` | 流式输出分块 |
| `test_stream_with_temperature_override` | 流式温度覆盖 |
| `test_ainvoke_returns_string` | 异步调用返回字符串 |

### test_llm_utils.py - LLM 工具函数测试

**测试类**: `TestSafeLlmCall` (6 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_safe_llm_call_success` | 成功调用返回结果 |
| `test_safe_llm_call_returns_none_on_error` | 错误时返回 None |
| `test_safe_llm_call_logs_error` | 错误日志记录 |
| `test_safe_llm_call_with_callback_success` | 成功回调执行 |
| `test_safe_llm_call_with_callback_error` | 错误回调执行 |
| `test_safe_llm_call_timeout` | 超时处理 |

### test_memory_manager.py - MemoryManager 单元测试

**测试类**: 8 个测试类，47 个测试

#### TestSessionMemory (10 个测试)
- `test_init_default_values` - 默认值初始化（含 checkpoint_summaries 空列表）
- `test_add_message` - 添加消息
- `test_get_recent_messages` - 获取最近消息
- `test_should_update_summary_no_messages` - 无消息不更新摘要
- `test_should_update_summary_interval_passed` - 间隔过更新摘要
- `test_should_update_summary_interval_not_passed` - 间隔未到不更新
- `test_get_agent_context` - 获取 agent 上下文
- `test_clear_message_history_empties_list` - clear_message_history 清空消息列表
- `test_clear_message_history_resets_last_summary_update` - clear_message_history 重置摘要更新计数
- `test_clear_message_history_preserves_checkpoint_summaries` - clear_message_history 保留检查点摘要

#### TestSessionMemoryClearHistory (3 个测试)
- `test_clear_message_history_empties_list` - 清空消息历史列表
- `test_clear_message_history_resets_last_summary_update` - 重置 last_summary_update 为 0
- `test_clear_message_history_preserves_checkpoint_summaries` - 清空时保留 checkpoint_summaries

#### TestSessionMemoryGetFullContext (5 个测试)
- `test_get_full_context_includes_topic` - 包含教学主题
- `test_get_full_context_includes_checkpoint_summaries` - 包含各检查点摘要
- `test_get_full_context_includes_teaching_summary` - 包含教学摘要
- `test_get_full_context_includes_recent_messages` - 包含最近消息
- `test_get_full_context_empty_state` - 空状态返回基本结构

#### TestTeacherAgentMemory (5 个测试)
- `test_init_default_values` - 默认值初始化
- `test_record_covered_topic` - 记录已讲授主题
- `test_record_student_question` - 记录学生问题
- `test_record_student_participation` - 记录学生参与
- `test_record_misconception` - 记录学生误解

#### TestStudentAgentMemory (5 个测试)
- `test_init_default_values` - 默认值初始化
- `test_from_profile` - 从 profile 创建
- `test_should_remember_concept_high_ability` - 高学习能力记住概念
- `test_should_remember_concept_low_ability` - 低学习能力可能忘记
- `test_update_knowledge` - 更新知识

#### TestMemoryManager (8 个测试)
- `test_init_creates_memories` - 初始化创建记忆
- `test_get_session_memory` - 获取会话记忆
- `test_get_teacher_memory` - 获取教师记忆
- `test_get_student_memory` - 获取学生记忆
- `test_update_session_memory` - 更新会话记忆
- `test_update_teacher_memory` - 更新教师记忆
- `test_update_student_memory` - 更新学生记忆
- `test_get_all_contexts` - 获取所有上下文

#### TestMemoryManagerSummary (7 个测试)
- `test_generate_summary_no_messages` - 无消息时摘要
- `test_generate_summary_with_messages` - 有消息时摘要
- `test_generate_summary_respects_max_length` - 摘要长度限制
- `test_should_update_summary_true` - 应该更新摘要
- `test_should_update_summary_false` - 不应更新摘要
- `test_update_summary_if_needed` - 按需更新摘要
- `test_get_teaching_progress` - 获取教学进度

#### TestMemoryManagerSummarizeCheckpoint (7 个测试)
- `test_summarize_checkpoint_appends_summary` - 摘要追加到 checkpoint_summaries
- `test_summarize_checkpoint_clears_message_history` - 摘要后清空消息历史
- `test_summarize_checkpoint_resets_last_summary_update` - 重置摘要更新计数
- `test_summarize_checkpoint_empty_history_returns_none` - 空历史返回 None
- `test_summarize_checkpoint_no_summary_fn_returns_none` - 无摘要函数返回 None
- `test_summarize_checkpoint_summary_failure_still_clears_history` - 摘要失败仍清空历史（try/finally）
- `test_summarize_checkpoint_accumulates_multiple_summaries` - 多次调用累积摘要

### test_name_pool.py - NamePool 服务测试

**测试**: 2 个函数测试

| 测试名称 | 验证内容 |
|---------|---------|
| `test_name_pool_initialization` | NamePool 初始化 |
| `test_get_random_name` | 随机名字获取 |

### test_schemas.py - Pydantic Schema 验证测试

**测试类**: 6 个测试类，25 个测试

#### TestStudentProfile (7 个测试)
- `test_valid_student_profile` - 有效学生配置
- `test_name_too_short` - 名字太短
- `test_name_too_long` - 名字太长
- `test_name_whitespace_only` - 纯空白格名字
- `test_learning_ability_out_of_range_low` - 学习能力过低
- `test_learning_ability_out_of_range_high` - 学习能力过高
- `test_default_values` - 默认值

#### TestRandomClassConfig (4 个测试)
- `test_valid_random_config` - 有效随机配置
- `test_level_distribution_not_sum_to_one` - 分布比例不等于 1
- `test_total_students_too_small` - 学生数太少
- `test_total_students_too_large` - 学生数太多

#### TestTeachingSessionCreate (4 个测试)
- `test_valid_session_create` - 有效会话创建
- `test_topic_too_long` - 主题太长
- `test_duration_too_short` - 时长太短
- `test_optional_duration` - 可选时长

#### TestMessage (4 个测试)
- `test_valid_message` - 有效消息
- `test_content_empty` - 内容为空
- `test_message_create_with_session_id` - 带会话 ID
- `test_message_with_receiver` - 带 receiver 字段的消息

#### TestWebSocketEventSchemas (6 个测试)
- `test_ws_connected_event` - WebSocket 连接确认事件
- `test_ws_message_event` - WebSocket 消息事件
- `test_ws_checkpoint_state_event` - WebSocket 检查点状态变更事件
- `test_ws_session_end_event` - WebSocket 会话结束事件
- `test_ws_student_answer_event` - WebSocket 学生回答事件
- `test_ws_session_state_event` - WebSocket 会话状态事件

#### TestMessageModelReceiver (1 个测试)
- `test_message_model_has_receiver_column` - MessageModel 有 receiver 列

### test_settings.py - 配置加载测试

**测试类**: 4 个测试类，11 个测试

#### TestLoadYaml (2 个测试)
- `test_load_app_config` - 加载应用配置
- `test_load_llm_config` - 加载 LLM 配置

#### TestTimezoneConfig (2 个测试)
- `test_timezone_default` - 默认时区
- `test_timezone_from_env` - 环境变量时区

#### TestTeachingTemperatures (3 个测试)
- `test_teaching_temperatures_exist` - 教学温度存在
- `test_temperature_ranges_valid` - 温度范围有效
- `test_temperature_mode_mapping` - 温度模式映射

#### TestStudentRespondProbabilities (4 个测试)
- `test_respond_probabilities_exist` - 响应概率存在
- `test_probabilities_sum_to_one` - 概率和为 1
- `test_attitude_ordering` - 态度排序
- `test_probability_mappings` - 概率映射

### test_student_agent.py - StudentAgent 单元测试

**测试类**: 7 个测试类，29 个测试

#### TestStudentAgentInit (4 个测试)
- `test_init_with_required_params` - 必需参数初始化
- `test_init_from_profile_creates_memory` - 从 profile 创建记忆
- `test_init_with_existing_memory` - 使用现有记忆
- `test_init_with_custom_rng` - 自定义随机数生成器

#### TestStudentAgentShouldRespond (4 个测试)
- `test_active_attitude_high_respond_probability` - 主动态度高响应率
- `test_neutral_attitude_medium_respond_probability` - 中立态度中响应率
- `test_passive_attitude_low_respond_probability` - 被动态度低响应率
- `test_should_respond_returns_bool` - 返回布尔值

#### TestStudentAgentAnswerQuestion (7 个测试)
- `test_answer_question_calls_llm` - 调用 LLM
- `test_answer_question_includes_question_in_prompt` - prompt 包含问题
- `test_answer_question_includes_student_context` - prompt 包含学生上下文
- `test_answer_question_excellent_level_prompt` - 优秀水平 prompt
- `test_answer_question_basic_level_prompt` - 基础水平 prompt
- `test_answer_question_returns_str` - 返回字符串
- `test_answer_question_records_message` - 记录消息

#### TestStudentAgentAskQuestion (4 个测试)
- `test_ask_question_calls_llm` - 调用 LLM
- `test_ask_question_includes_teaching_context` - prompt 包含教学上下文
- `test_ask_question_returns_str` - 返回字符串
- `test_ask_question_records_message_type` - 记录消息类型

#### TestStudentAgentSubmitHomework (5 个测试)
- `test_submit_homework_calls_llm` - 调用 LLM
- `test_submit_homework_includes_assignment` - prompt 包含作业
- `test_submit_homework_includes_student_context` - prompt 包含学生上下文
- `test_submit_homework_returns_str` - 返回字符串
- `test_submit_homework_records_message` - 记录消息

#### TestStudentAgentGiveFeedback (5 个测试)
- `test_give_feedback_calls_llm` - 调用 LLM
- `test_give_feedback_includes_feedback_request` - prompt 包含反馈请求
- `test_give_feedback_includes_student_context` - prompt 包含学生上下文
- `test_give_feedback_returns_str` - 返回字符串
- `test_give_feedback_records_message` - 记录消息

#### TestStudentAgentEmptyContent (2 个测试)
- `test_answer_question_empty_content_raises_error` - 空内容抛出错误
- `test_ask_question_empty_content_raises_error` - 空内容抛出错误

### test_student_factory.py - StudentFactory 单元测试

**测试类**: 3 个测试类，13 个测试

#### 函数测试 (4 个)
- `test_create_students_manual` - 手动创建学生
- `test_create_students_random` - 随机创建学生
- `test_create_students_json` - JSON 导入创建
- `test_export_students` - 导出学生 JSON

#### TestStudentFactoryErrors (4 个测试)
- `test_empty_name_list_raises_error` - 空名字列表错误
- `test_duplicate_names_in_list` - 重复名字错误
- `test_invalid_json_format` - 无效 JSON 格式
- `test_invalid_student_data` - 无效学生数据

#### TestStudentFactoryReproducibility (2 个测试)
- `test_json_roundtrip_preserves_data` - JSON 往返保留数据
- `test_random_with_seed_is_deterministic` - 随机种子确定性

#### TestStudentFactoryDistribution (3 个测试)
- `test_random_respects_level_distribution` - 遵守水平分布
- `test_random_respects_attitude_distribution` - 遵守态度分布
- `test_random_total_count_matches` - 总数匹配

### test_teacher_agent.py - TeacherAgent 单元测试

**测试类**: 13 个测试类，37 个测试

#### TestTeacherAgentInit (1 个测试)
- `test_init_with_required_params` - 必需参数初始化

#### TestTeacherAgentLecture (2 个测试)
- `test_deliver_lecture_generates_content` - 生成讲授内容
- `test_deliver_lecture_records_message` - 记录消息

#### TestTeacherAgentContentComplete (2 个测试)
- `test_content_complete_returns_true_when_enough_content` - 足够内容返回 true
- `test_content_complete_returns_false_when_insufficient` - 内容不足返回 false

#### TestTeacherAgentDeliverLectureErrors (2 个测试)
- `test_deliver_lecture_empty_topic_raises_error` - 空主题抛出错误
- `test_deliver_lecture_invalid_teaching_mode_raises_error` - 无效模式抛出错误

#### TestTeacherAgentStreamErrors (2 个测试)
- `test_deliver_lecture_stream_empty_topic_raises_error` - 空主题抛出错误
- `test_deliver_lecture_stream_invalid_mode_raises_error` - 无效模式抛出错误

#### TestTeacherAgentCheckpointQuestion (3 个测试)
- `test_checkpoint_question_calls_llm` - 调用 LLM
- `test_checkpoint_question_includes_context` - 包含上下文
- `test_checkpoint_question_records_message` - 记录消息

#### TestTeacherAgentDiscussionQuestion (3 个测试)
- `test_discussion_question_calls_llm` - 调用 LLM
- `test_discussion_question_includes_context` - 包含上下文
- `test_discussion_question_records_message` - 记录消息

#### TestTeacherAgentReplyToStudent (4 个测试)
- `test_reply_to_student_calls_llm` - 调用 LLM
- `test_reply_to_student_includes_question` - 包含问题
- `test_reply_to_student_may_choose_not_to_respond` - 可能选择不响应
- `test_reply_to_student_records_message` - 记录消息

#### TestTeacherAgentAssignHomework (3 个测试)
- `test_assign_homework_calls_llm` - 调用 LLM
- `test_assign_homework_includes_context` - 包含上下文
- `test_assign_homework_records_message` - 记录消息

#### TestTeacherAgentGradeHomework (3 个测试)
- `test_grade_homework_calls_llm` - 调用 LLM
- `test_grade_homework_includes_submission` - 包含提交内容
- `test_grade_homework_returns_feedback` - 返回反馈

#### TestTeacherAgentEndFeedback (3 个测试)
- `test_end_feedback_calls_llm` - 调用 LLM
- `test_end_feedback_includes_summary` - 包含摘要
- `test_end_feedback_records_message` - 记录消息

#### TestEndFeedbackWithContextIsolation (4 个测试)
- `test_end_feedback_uses_full_context_not_agent_context` - end_feedback 使用 get_full_context 而非完整 system prompt
- `test_end_feedback_uses_lightweight_context` - end_feedback 使用轻量级上下文（检查点摘要 + 最近消息）
- `test_build_end_feedback_context` - _build_end_feedback_context 构建正确的上下文
- `test_end_feedback_records_message_to_history` - end_feedback 消息记录到 message_history（回归测试）

#### TestTeacherAgentNewMethodsErrors (7 个测试)
- `test_answer_checkpoint_empty_question_error` - 空问题错误
- `test_assign_homework_empty_topic_error` - 空主题错误
- `test_grade_homework_empty_submission_error` - 空提交错误
- `test_grade_homework_empty_homework_error` - 空作业错误
- `test_reply_to_student_empty_question_error` - 空问题错误
- `test_reply_to_student_empty_name_error` - 空名字错误
- `test_end_feedback_empty_topic_error` - 空主题错误

### test_teacher_controller.py - TeacherSessionController 单元测试

**测试类**: 11 个测试类，17 个测试

TeacherSessionController 是教师模式核心控制器，用户扮演教师角色控制教学流程。

#### TestTeacherSessionControllerInit (1 个测试)
- `test_init_creates_controller_with_required_components` - 初始化创建控制器及其必需组件

#### TestHandleBroadcastLecture (1 个测试)
- `test_handle_broadcast_lecture_records_to_memory` - 测试广播讲授内容记录到记忆系统

#### TestHandleAskToAll (1 个测试)
- `test_handle_ask_to_all_collects_responses_from_all_students` - 测试向全体提问收集所有学生回答

#### TestHandleAskToStudent (2 个测试)
- `test_handle_ask_to_student_collects_response_from_target_student` - 测试向单个学生提问收集该学生的回答
- `test_handle_ask_to_student_with_nonexistent_student_does_not_crash` - 测试向不存在的学生提问不会崩溃

#### TestHandleTeacherReply (3 个测试)
- `test_handle_teacher_reply_records_reply_to_memory` - 测试教师回复记录到记忆系统
- `test_handle_teacher_reply_tracks_dialogue_round_count` - 测试教师回复增加对话轮数
- `test_handle_teacher_reply_sets_active_dialogue_state` - 测试教师回复设置活跃对话状态

#### TestHandleEndDialogue (4 个测试)
- `test_handle_end_dialogue_clears_active_dialogue_state` - 测试结束对话清除活跃对话状态
- `test_handle_end_dialogue_triggers_observer_learning` - 测试结束对话触发旁听学习
- `test_handle_end_dialogue_with_zero_rounds_does_not_trigger_observer_learning` - 测试零轮对话结束不触发旁听学习

#### TestHandleAdvanceCheckpoint (2 个测试)
- `test_handle_advance_checkpoint_clears_active_dialogue` - 测试推进检查点强制结束当前对话
- `test_handle_advance_checkpoint_with_no_active_dialogue` - 测试没有活跃对话时推进检查点不触发旁听学习

#### TestHandleAssignHomework (1 个测试)
- `test_handle_assign_homework_records_to_memory` - 测试布置作业记录到记忆系统

#### TestHandleCollectHomework (2 个测试)
- `test_handle_collect_homework_collects_submissions_from_all_students` - 测试收集所有学生作业提交
- `test_handle_collect_homework_with_student_without_submission` - 测试有学生未提交作业时的处理

**运行命令**:
```bash
pytest tests/units/test_teacher_controller.py -v
```

### test_connection_manager.py - ConnectionManager WebSocket 连接池测试

**测试类**: `TestConnectionManager` (11 个测试)

ConnectionManager 管理 WebSocket 连接池，按 session_id 分组，支持广播和个人消息，自动清理断开的连接。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_init_empty` | 初始化时连接池为空 |
| `test_connect_adds_connection` | connect() 将 WebSocket 添加到指定 session |
| `test_connect_multiple_sessions` | 不同 session 的连接分开管理 |
| `test_connect_same_session_multiple_clients` | 同一 session 可以有多个客户端连接 |
| `test_disconnect_removes_connection` | disconnect() 从连接池中移除 WebSocket |
| `test_broadcast_to_session` | broadcast() 向指定 session 的所有连接发送消息 |
| `test_broadcast_empty_session` | broadcast() 对没有连接的 session 不报错 |
| `test_broadcast_removes_dead_connection` | broadcast() 自动移除发送失败的连接 |
| `test_send_personal_message` | send_personal() 向指定连接发送消息 |
| `test_disconnect_nonexistent_connection` | 断开不存在的连接不报错 |
| `test_send_personal_dead_connection` | 向已断开的连接发送消息不报错 |
| `test_get_connection_count` | get_connection_count() 返回指定 session 的连接数 |

**运行命令**:
```bash
pytest tests/units/test_connection_manager.py -v
```

### test_session_registry.py - SessionRegistry 会话注册表测试

**测试类**: `TestSessionRegistry` (4 个测试), `TestSessionRegistryTypes` (6 个测试)

SessionRegistry 映射 session_id 到运行中的 SessionOrchestrator 或 TeacherSessionController 实例。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_register_and_get_orchestrator` | 注册并获取观察模式 orchestrator |
| `test_register_and_get_controller` | 注册并获取教师模式 controller |
| `test_get_nonexistent_session` | 获取不存在的 session 返回 None |
| `test_unregister` | 注销 session |
| `test_get_orchestrator_none_for_teacher_session` | 教师模式 get_orchestrator 返回 None |
| `test_get_controller_none_for_observation_session` | 观察模式 get_controller 返回 None |
| `test_get_session_info_observation` | 观察模式 get_session_info 返回 mode='observation' |
| `test_get_session_info_teacher` | 教师模式 get_session_info 返回 mode='teacher' |
| `test_get_session_info_not_found` | 不存在的 session get_session_info 返回 None |
| `test_unregister_clears_session_modes` | 注销后 get_session_info 返回 None |

**运行命令**:
```bash
pytest tests/units/test_session_registry.py -v
```

### test_ws_command_router.py - WebSocket 命令 schema 和路由测试

**测试类**: `TestWsCommandSchemas` (13 个测试), `TestWsCommandRouter` (10 个测试)

测试 WebSocket 命令的 Pydantic schema 验证和命令路由到 controller 的逻辑。

**TestWsCommandSchemas** — 命令 schema 验证:

| 测试名称 | 验证内容 |
|---------|---------|
| `test_broadcast_lecture_command_valid` | 合法的 broadcast_lecture 命令 |
| `test_broadcast_lecture_command_missing_content` | 缺少 content 字段报错 |
| `test_ask_to_all_command_valid` | 合法的 ask_to_all 命令 |
| `test_ask_to_all_command_missing_question` | 缺少 question 字段报错 |
| `test_ask_to_student_command_valid` | 合法的 ask_to_student 命令 |
| `test_ask_to_student_command_missing_fields` | 缺少 student_name 字段报错 |
| `test_teacher_reply_command_valid` | 合法的 teacher_reply 命令 |
| `test_advance_checkpoint_command_valid` | 合法的 advance_checkpoint 命令 |
| `test_end_dialogue_command_valid` | 合法的 end_dialogue 命令 |
| `test_assign_homework_command_valid` | 合法的 assign_homework 命令 |
| `test_collect_homework_command_valid` | 合法的 collect_homework 命令 |
| `test_end_teaching_command_valid` | 合法的 end_teaching 命令 |
| `test_unknown_command_type_rejected` | 未知命令类型报错 |

**TestWsCommandRouter** — 命令路由测试:

| 测试名称 | 验证内容 |
|---------|---------|
| `test_broadcast_lecture_routes_to_controller` | broadcast_lecture 路由到 controller |
| `test_ask_to_all_routes_to_controller` | ask_to_all 路由到 controller |
| `test_unknown_command_returns_error` | 未知命令返回 error |
| `test_no_session_returns_error` | session 不存在返回 error |
| `test_advance_checkpoint_routes_to_controller` | advance_checkpoint 路由到 controller |
| `test_command_result_pushed_via_websocket` | 命令结果通过 WebSocket 推送 |
| `test_end_dialogue_routes_to_controller` | end_dialogue 路由到 controller |
| `test_assign_homework_routes_to_controller` | assign_homework 路由到 controller |
| `test_collect_homework_routes_to_controller` | collect_homework 路由到 controller |
| `test_end_teaching_routes_to_controller` | end_teaching 路由到 controller |

**运行命令**:
```bash
pytest tests/units/test_ws_command_router.py -v
```

### test_orchestrator_ws_push.py - SessionOrchestrator WebSocket 推送测试

**测试类**: `TestOrchestratorWsPush` (2 个测试)

测试 SessionOrchestrator 通过 ConnectionManager 广播检查点状态变更事件。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_ws_push_uses_connection_manager` | _ws_push_checkpoint_state 通过 ConnectionManager 广播消息 |
| `test_ws_push_skips_when_no_connections` | 没有活跃连接时跳过 broadcast |

**运行命令**:
```bash
pytest tests/units/test_orchestrator_ws_push.py -v
```

### test_session_orchestrator.py (unit_llm) - SessionOrchestrator 单元测试（Mock LLM）

**测试类**: `TestCheckpointContextIsolation` (2 个测试)

测试 SessionOrchestrator 检查点完成后的上下文隔离机制。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_teach_checkpoint_clears_message_history` | _teach_checkpoint 完成后清除消息历史并保存摘要 |
| `test_multiple_checkpoints_accumulate_summaries` | 多个检查点依次推进时累积所有摘要 |

**运行命令**:
```bash
pytest tests/unit_llm/test_session_orchestrator.py -v
```

### test_teacher_controller_ws_push.py - TeacherSessionController WebSocket 推送测试

**测试类**: `TestTeacherControllerWsPush` (2 个测试)

测试 TeacherSessionController 通过 ConnectionManager 广播教师讲授和学生回答事件。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_handle_ask_to_all_broadcasts_answers` | handle_ask_to_all 通过 ConnectionManager 广播学生回答 |
| `test_handle_broadcast_lecture_pushes_message` | handle_broadcast_lecture 通过 ConnectionManager 推送消息 |

**运行命令**:
```bash
pytest tests/units/test_teacher_controller_ws_push.py -v
```

---

## 集成测试详解

### test_alembic_migration.py - Alembic 数据库迁移测试

**测试类**: `TestAlembicMigration` (7 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_database_file_exists` | 数据库文件存在 |
| `test_all_tables_exist` | 所有表已创建（teaching_sessions, session_memories, teacher_memories, messages, student_memories, checkpoint_plans） |
| `test_teaching_sessions_structure` | teaching_sessions 表结构正确 |
| `test_session_memories_structure` | session_memories 表结构正确 |
| `test_messages_structure` | messages 表结构正确（含 receiver 列） |
| `test_teacher_memories_structure` | teacher_memories 表结构正确 |
| `test_foreign_keys_exist_in_schema` | 外键约束在 schema 中定义 |

**运行命令**:
```bash
pytest tests/integration/test_alembic_migration.py -v
```

### test_checkpoint_api.py - Checkpoint API 集成测试

**测试类**: `TestCheckpointAPI` (6 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_create_checkpoint_plan` | 创建检查点计划 |
| `test_get_checkpoint_plan` | 获取检查点计划 |
| `test_update_checkpoint_state` | 更新检查点状态 |
| `test_advance_checkpoint` | 推进检查点 |
| `test_delete_checkpoint_plan` | 删除检查点计划 |
| `test_get_nonexistent_plan_returns_404` | 不存在计划返回 404 |

**运行命令**:
```bash
pytest tests/integration/test_checkpoint_api.py -v
```

### test_checkpoint_service_real.py - 真实 LLM Checkpoint 生成测试

**测试类**: `TestCheckpointPlanServiceReal` (5 个测试，需真实 LLM API)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_generate_plan_didactic_mode` | 灌输式模式生成 |
| `test_generate_plan_heuristic_mode` | 启发式模式生成 |
| `test_generate_plan_discussion_mode` | 讨论式模式生成 |
| `test_generate_plan_serialize_to_json` | JSON 序列化 |
| `test_generate_plan_edge_cases` | 边界情况 |

**运行命令** (需要网络和 API key):
```bash
pytest tests/integration/test_checkpoint_service_real.py -v -s -m integration
```

**注意**: 此测试需要真实 LLM API，使用 `@pytest.mark.integration` 标记。

### test_database.py - 数据库集成测试

**测试类**: 4 个测试类，7 个测试

#### TestTeachingSessionModel (2 个测试)
- `test_create_teaching_session` - 创建教学会话
- `test_read_teaching_session` - 读取教学会话

#### TestMessageModel (2 个测试)
- `test_create_message` - 创建消息
- `test_message_session_relationship` - 消息会话关系

#### TestSessionMemoryModel (1 个测试)
- `test_create_session_memory` - 创建会话记忆

#### TestTeacherMemoryModel (1 个测试)
- `test_create_teacher_memory` - 创建教师记忆

#### TestStudentMemoryModel (1 个测试)
- `test_create_student_memory` - 创建学生记忆

### test_memory_persistence.py - 记忆持久化集成测试

**测试类**: 4 个测试类，17 个测试

#### TestMemoryPersistenceSave (7 个测试)
- `test_save_session_memory_create` - 首次保存会话记忆（创建）
- `test_save_session_memory_update` - 更新已有的会话记忆
- `test_save_teacher_memory_create` - 首次保存教师记忆
- `test_save_teacher_memory_update` - 更新已有的教师记忆
- `test_save_student_memory_create` - 首次保存学生记忆
- `test_save_student_memory_update` - 更新已有的学生记忆
- `test_save_message` - 保存单条消息

#### TestMemoryPersistenceLoad (7 个测试)
- `test_load_session_memory_exists` - 加载已存在的会话记忆
- `test_load_session_memory_not_exists` - 加载不存在的会话记忆返回 None
- `test_load_session_memory_with_messages` - 加载会话记忆包含消息历史
- `test_load_teacher_memory_exists` - 加载已存在的教师记忆
- `test_load_teacher_memory_not_exists` - 加载不存在的教师记忆返回 None
- `test_load_student_memory_exists` - 加载已存在的学生记忆
- `test_load_student_memory_not_exists` - 加载不存在的学生记忆返回 None

#### TestMemoryIntegration (2 个测试)
- `test_end_to_end_memory_workflow` - 端到端记忆工作流
- `test_cascade_delete_session` - 级联删除会话

#### TestCheckpointSummariesPersistence (1 个测试)
- `test_save_and_load_checkpoint_summaries` - checkpoint_summaries 的保存和加载

### test_student_memory_migration.py - 学生记忆迁移测试

**测试类**: `TestStudentMemoryMigration` (3 个测试)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_migrate_student_memory_to_v2` | 迁移学生记忆到 v2 |
| `test_migration_preserves_learned_concepts` | 迁移保留已学概念 |
| `test_migration_preserves_name` | 迁移保留名字 |

### test_teacher_agent_real.py - 教师 Agent 真实 LLM 测试

**测试类**: `TestTeacherAgentRealLecture` (3 个测试，需真实 LLM API)

| 测试名称 | 验证内容 |
|---------|---------|
| `test_deliver_lecture_didactic` | 灌输式讲授 |
| `test_deliver_lecture_heuristic` | 启发式讲授 |
| `test_deliver_lecture_discussion` | 讨论式讲授 |

**运行命令** (需要网络和 API key):
```bash
pytest tests/integration/test_teacher_agent_real.py -v -s -m integration
```

### test_teacher_controller_full_classroom.py - TeacherSessionController 全课堂流程集成测试

**测试类**: 3 个测试类，3 个集成测试

TeacherSessionController 全课堂流程集成测试，使用 Mock 对象模拟学生行为。

#### TestTeacherControllerFullClassroomFlow (1 个测试)
- `test_full_classroom_teaching_flow` - 测试完整课堂教学流程：讲授 → 提问 → 对话 → 作业

#### TestMultiRoundDialogueFlow (1 个测试)
- `test_multi_round_dialogue_flow` - 测试多轮对话流程

#### TestErrorPathStudentNotFound (1 个测试)
- `test_error_path_student_not_found` - 测试错误路径：向不存在的学生提问

**运行命令**:
```bash
pytest tests/integration/test_teacher_controller_full_classroom.py -v
```

### test_websocket.py - WebSocket 端点集成测试

**测试类**: `TestWebSocketConnection` (3 个测试), `TestWebSocketCommandIntegration` (4 个测试)

测试 WebSocket 端点 `/ws/sessions/{session_id}` 的连接建立、心跳、命令路由。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_websocket_connect_and_receive_connected_event` | 连接后收到 connected 事件 |
| `test_websocket_ping_pong` | ping/pong 心跳机制 |
| `test_websocket_disconnect_handling` | 客户端断开时服务端不崩溃 |
| `test_broadcast_lecture_command_via_websocket` | broadcast_lecture 命令路由到 controller |
| `test_unknown_command_returns_error_via_websocket` | 未知命令返回 error |
| `test_command_to_nonexistent_session_returns_error` | 未注册 session 返回 error |
| `test_observation_mode_rejects_commands` | 观察模式拒绝教师命令 |

**运行命令**:
```bash
pytest tests/integration/test_websocket.py -v
```

### test_session_api.py - 会话管理 API 集成测试

**测试**: 2 个函数测试

测试会话管理 REST API 端点。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_get_messages_empty_session` | 查询不存在 session 的消息返回空列表 |
| `test_get_session_status_not_found` | 查询不存在的 session 返回 404 |

**运行命令**:
```bash
pytest tests/integration/test_session_api.py -v
```

### test_observation_api.py - 观察模式 API 集成测试

**测试**: 3 个函数测试, 1 个异步测试类 `TestObservationApiRegistration`

测试观察模式启动 API 端点 `POST /observation/start`。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_start_observation_creates_session` | 启动观察模式创建 teaching_session 记录 |
| `test_start_observation_missing_topic` | 缺少 topic 参数返回 422 |
| `test_start_observation_empty_students` | 空学生列表返回 422 |
| `test_start_observation_registers_orchestrator` | 完整初始化流程并注册到 SessionRegistry |

**运行命令**:
```bash
pytest tests/integration/test_observation_api.py -v
```

### test_teacher_controller_api.py - TeacherController REST API 集成测试

**测试类**: `TestTeacherControllerAPI` (4 个测试)

测试教师模式的检查点计划 REST API 端点。

| 测试名称 | 验证内容 |
|---------|---------|
| `test_get_checkpoint_plan_returns_plan` | 获取检查点计划返回正确数据 |
| `test_edit_checkpoint_plan_modifies_plan` | 编辑检查点计划修改成功 |
| `test_edit_checkpoint_plan_fails_when_teaching_started` | 教学已开始时不能编辑计划 |
| `test_edit_checkpoint_plan_fails_when_plan_not_found` | 计划不存在时编辑失败 |

**运行命令**:
```bash
pytest tests/integration/test_teacher_controller_api.py -v
```

---

## 运行特定测试

### 按功能模块运行

```bash
# 检查点系统测试
pytest tests/units/test_checkpoint*.py tests/integration/test_checkpoint*.py -v

# LLM 相关测试
pytest tests/units/test_llm*.py -v

# 记忆系统测试
pytest tests/units/test_memory_manager.py tests/integration/test_memory*.py -v

# 学生相关测试
pytest tests/units/test_student*.py tests/integration/test_student*.py -v

# 教师 Agent 测试
pytest tests/units/test_teacher_agent.py tests/integration/test_teacher_agent_real.py -v

# 教师 Controller 测试
pytest tests/units/test_teacher_controller.py tests/integration/test_teacher_controller_full_classroom.py -v

# WebSocket 通信测试
pytest tests/units/test_connection_manager.py tests/units/test_session_registry.py tests/units/test_orchestrator_ws_push.py tests/units/test_teacher_controller_ws_push.py tests/integration/test_websocket.py -v

# 会话管理 API 测试
pytest tests/integration/test_session_api.py tests/integration/test_observation_api.py -v
```

### 按测试类型运行

```bash
# 只运行单元测试
pytest tests/units/ -v

# 只运行集成测试
pytest tests/integration/ -v

# 运行所有测试（排除集成测试）
pytest tests/ -v -m "not integration"

# 运行真实 LLM 集成测试
pytest -m integration -v
```

### 按测试名称运行

```bash
# 运行所有名字包含 "checkpoint" 的测试
pytest -k checkpoint -v

# 运行所有名字包含 "memory" 的测试
pytest -k memory -v

# 运行所有名字包含 "agent" 的测试
pytest -k agent -v
```

---

## 下一步

待实现的测试文件：

- [ ] `tests/integration/test_full_teaching_flow.py` - 完整教学流程集成测试
- [ ] `tests/integration/test_checkpoint_flow.py` - 检查点流程端到端测试
