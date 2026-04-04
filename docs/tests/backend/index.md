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
├── __init__.py           # 测试模块初始化
├── conftest.py           # pytest 配置和 fixtures
├── test_database.py      # 数据库 ORM 测试
└── test_schemas.py       # Pydantic schema 验证测试
```

---

## Pytest Fixtures

项目定义了以下 fixtures（在 `tests/conftest.py`）：

### event_loop
- **作用**: 创建事件循环
- **范围**: session
- **用途**: 异步测试支持

```python
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

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
    from orm.message import MessageModel  # noqa: F401
    from orm.session_memory import SessionMemoryModel  # noqa: F401
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

## 下一步

待实现的测试文件：

- [ ] `tests/test_memory_manager.py` - MemoryManager 测试
- [ ] `tests/test_student_factory.py` - StudentFactory 测试
- [ ] `tests/test_teacher_agent.py` - 教师 Agent 测试
- [ ] `tests/test_session_orchestrator.py` - SessionOrchestrator 测试
- [ ] `tests/test_api.py` - API 端点集成测试
