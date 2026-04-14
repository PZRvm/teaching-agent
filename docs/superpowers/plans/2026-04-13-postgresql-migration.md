# PostgreSQL 数据库迁移 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将后端数据库从 SQLite 迁移到 PostgreSQL，保持所有业务逻辑不变。

**Architecture:** 替换异步数据库驱动（aiosqlite → asyncpg），通过环境变量管理数据库连接，重置 Alembic 迁移基线。ORM 模型零改动（已使用 SQLAlchemy 通用类型，自动映射 PostgreSQL 原生 JSONB/ENUM）。测试继续使用 SQLite 内存数据库。

**Tech Stack:** SQLAlchemy 2.0.48, asyncpg, psycopg2-binary, Alembic 1.18.4, pytest-asyncio

---

### Task 1: 更新 Python 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 替换数据库驱动依赖**

将 `requirements.txt` 中的 `aiosqlite` 替换为 `asyncpg` 和 `psycopg2-binary`：

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.34.0

langchain==1.2.14
langchain-core==1.2.24
langchain-community==0.4.1
langchain-openai==1.1.12
openai==2.30.0
tiktoken==0.12.0
chromadb==1.5.5

SQLAlchemy==2.0.48
alembic==1.18.4
aiosqlite>=0.22.1  # 测试使用 SQLite 内存数据库
asyncpg>=0.30.0
psycopg2-binary>=2.9.0
greenlet==3.3.2
python-dotenv==1.0.1
pydantic-settings==2.13.1
pyyaml==6.0.2

# 开发工具
ruff==0.9.9

# 测试框架
pytest>=8.2
pytest-asyncio>=0.24
pytest-cov>=5.0
pytest-mock>=3.14
httpx>=0.27  # For async HTTP testing in FastAPI
```

变更说明：
- 保留 `aiosqlite>=0.22.1`（测试继续使用 SQLite 内存数据库，需要此驱动）
- 添加 `asyncpg>=0.30.0`（PostgreSQL 异步驱动）
- 添加 `psycopg2-binary>=2.9.0`（Alembic 同步迁移需要）

- [ ] **Step 2: 安装新依赖**

Run: `cd backend && pip install -r requirements.txt`
Expected: 所有包安装成功，无报错

- [ ] **Step 3: 验证旧依赖已移除**

Run: `cd backend && python -c "import aiosqlite" 2>&1 | grep -q "ModuleNotFoundError" && echo "OK: aiosqlite removed" || echo "FAIL: aiosqlite still installed"`
Expected: `OK: aiosqlite removed`

- [ ] **Step 4: 验证新依赖可用**

Run: `cd backend && python -c "import asyncpg; print(f'asyncpg {asyncpg.__version__}')" && python -c "import psycopg2; print(f'psycopg2 {psycopg2.__version__}')"`
Expected: 两个版本号正常输出

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(deps): 将数据库驱动从 aiosqlite 切换到 asyncpg + psycopg2-binary"
```

---

### Task 2: 更新数据库配置文件

**Files:**
- Modify: `backend/configs/database.yml`
- Modify: `backend/.env.example`

- [ ] **Step 1: 更新 database.yml**

移除 SQLite 特定配置，保留连接池配置：

```yaml
# 数据库配置
database:
  # 连接池配置（PostgreSQL 生效）
  pool_size: 5
  max_overflow: 10
```

- [ ] **Step 2: 更新 .env.example**

添加 DATABASE_URL 环境变量：

```
# ============================================
# 教学智能体 - 环境变量配置
# ============================================
# 注意：大部分配置已在 configs/ 目录下的 YAML 文件中
# 此文件仅存放敏感信息（如 API 密钥）和运行时覆盖配置

# ============================================
# 数据库配置
# ============================================
# PostgreSQL 连接 URL（覆盖 configs/database.yml 中的默认值）
# 格式: postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
DATABASE_URL=postgresql+asyncpg://admin:123456@localhost:5432/mydb

# ============================================
# LLM API 配置
# ============================================
# 硅基流动 API Key（获取地址：https://siliconflow.cn）
OPENAI_API_KEY=your_siliconflow_api_key_here

# 如果使用其他 LLM 提供商，修改 configs/llm.yml 中的 base_url
```

- [ ] **Step 3: Commit**

```bash
git add backend/configs/database.yml backend/.env.example
git commit -m "chore(config): 更新 database.yml 和 .env.example 支持 PostgreSQL"
```

---

### Task 3: 更新 settings.py 加载数据库配置

**Files:**
- Modify: `backend/core/settings.py`

- [ ] **Step 1: 编写 settings.py 测试**

创建测试文件 `backend/tests/units/test_settings_database.py`：

```python
"""测试 settings.py 数据库配置加载."""

import os
from unittest.mock import patch

import pytest


class TestDatabaseSettings:
    """测试数据库配置从 YAML 和环境变量加载."""

    def test_database_url_from_yaml(self):
        """测试 DATABASE_URL 从 YAML 文件加载（无环境变量时使用默认值）."""
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        with patch.dict(os.environ, env, clear=False):
            # 需要重新加载模块以应用环境变量变更
            import importlib
            from core import settings
            importlib.reload(settings)
            # YAML 中的 url 已被移除，所以应该没有默认值
            # 验证 DATABASE_URL 属性存在
            assert hasattr(settings, "DATABASE_URL")
            assert isinstance(settings.DATABASE_URL, str)

    def test_database_url_from_env(self):
        """测试 DATABASE_URL 环境变量覆盖 YAML 配置."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://test:123@localhost/testdb"}):
            import importlib
            from core import settings
            importlib.reload(settings)
            assert settings.DATABASE_URL == "postgresql+asyncpg://test:123@localhost/testdb"

    def test_pool_settings_loaded(self):
        """测试连接池配置从 YAML 加载."""
        from core import settings
        assert hasattr(settings, "DATABASE_POOL_SIZE")
        assert isinstance(settings.DATABASE_POOL_SIZE, int)
        assert settings.DATABASE_POOL_SIZE == 5
        assert hasattr(settings, "DATABASE_MAX_OVERFLOW")
        assert isinstance(settings.DATABASE_MAX_OVERFLOW, int)
        assert settings.DATABASE_MAX_OVERFLOW == 10
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/units/test_settings_database.py -v`
Expected: FAIL — `settings` 模块没有 `DATABASE_URL`、`DATABASE_POOL_SIZE`、`DATABASE_MAX_OVERFLOW` 属性

- [ ] **Step 3: 实现 settings.py 数据库配置加载**

在 `backend/core/settings.py` 中添加数据库配置加载：

```python
"""应用配置 — 从 YAML 文件加载配置项."""

from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


def _load_yaml(filename: str) -> dict:
    """加载 configs/ 下的 YAML 配置文件."""
    config_path = Path(__file__).parents[1] / "configs" / filename
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if config is None:
        raise ValueError(f"配置文件 {filename} 为空或格式无效")
    return config


_APP = _load_yaml("app.yml")
_LLM = _load_yaml("llm.yml")
_DATABASE = _load_yaml("database.yml")

# 时区
TIMEZONE = ZoneInfo(_APP["app"]["timezone"])

# 教学模式 → 温度
TEACHING_TEMPERATURES: dict[str, float] = _LLM["teaching_temperatures"]

# 默认温度（教学模式未匹配时）
DEFAULT_TEACHING_TEMPERATURE: float = 0.3

# 内容完成度判断温度（需要高确定性）
CONTENT_JUDGE_TEMPERATURE: float = 0.1

# 学生态度 → 响应概率
STUDENT_RESPOND_PROBABILITIES: dict[str, float] = _LLM["student_respond_probabilities"]

# 默认响应概率（态度未匹配时）
DEFAULT_RESPOND_PROBABILITY: float = 0.5

# CORS 配置
CORS_ALLOW_ORIGINS: list[str] = _APP["app"]["cors"]["allow_origins"]
CORS_ALLOW_METHODS: list[str] = _APP["app"]["cors"]["allow_methods"]
CORS_ALLOW_HEADERS: list[str] = _APP["app"]["cors"]["allow_headers"]

# 数据库配置
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
DATABASE_POOL_SIZE: int = _DATABASE["database"].get("pool_size", 5)
DATABASE_MAX_OVERFLOW: int = _DATABASE["database"].get("max_overflow", 10)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/units/test_settings_database.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/core/settings.py backend/tests/units/test_settings_database.py
git commit -m "feat(config): settings.py 支持从环境变量加载 DATABASE_URL"
```

---

### Task 4: 更新 database.py 引擎配置

**Files:**
- Modify: `backend/core/database.py`

- [ ] **Step 1: 编写 database.py 测试**

创建测试文件 `backend/tests/units/test_database_engine.py`：

```python
"""测试 database.py 引擎配置."""

from unittest.mock import patch

import pytest


class TestDatabaseEngine:
    """测试数据库引擎配置."""

    @patch("core.database.settings")
    def test_engine_uses_settings_url(self, mock_settings):
        """测试引擎使用 settings.DATABASE_URL."""
        mock_settings.DATABASE_URL = "postgresql+asyncpg://test:123@localhost/testdb"
        mock_settings.DATABASE_POOL_SIZE = 5
        mock_settings.DATABASE_MAX_OVERFLOW = 10

        import importlib
        from core import database
        importlib.reload(database)

        assert database.async_engine.url.database == "testdb"
        assert database.async_engine.url.drivername == "postgresql+asyncpg"

    @patch("core.database.settings")
    def test_no_check_same_thread(self, mock_settings):
        """测试 PostgreSQL 引擎不包含 SQLite 特定的 connect_args."""
        mock_settings.DATABASE_URL = "postgresql+asyncpg://test:123@localhost/testdb"
        mock_settings.DATABASE_POOL_SIZE = 5
        mock_settings.DATABASE_MAX_OVERFLOW = 10

        import importlib
        from core import database
        importlib.reload(database)

        # PostgreSQL 不需要 check_same_thread 参数
        assert database.async_engine.url._queries == {} or "check_same_thread" not in str(
            database.async_engine.url
        )

    @patch("core.database.settings")
    def test_empty_database_url_raises_error(self, mock_settings):
        """测试空 DATABASE_URL 抛出 ValueError."""
        mock_settings.DATABASE_URL = ""
        mock_settings.DATABASE_POOL_SIZE = 5
        mock_settings.DATABASE_MAX_OVERFLOW = 10

        import importlib
        from core import database

        with pytest.raises(ValueError, match="DATABASE_URL"):
            importlib.reload(database)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd backend && python -m pytest tests/units/test_database_engine.py -v`
Expected: FAIL — 当前 `database.py` 硬编码 SQLite URL，没有使用 settings

- [ ] **Step 3: 实现 database.py PostgreSQL 引擎配置**

将 `backend/core/database.py` 替换为：

```python
"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.settings import DATABASE_URL, DATABASE_MAX_OVERFLOW, DATABASE_POOL_SIZE

# 验证数据库连接 URL 已配置
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL 未设置。请在 backend/.env 中配置 DATABASE_URL，"
        "例如: DATABASE_URL=postgresql+asyncpg://admin:123456@localhost:5432/mydb"
    )

# Create async engine
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=False,
)

# Create async session maker
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting async database sessions.

    Yields:
        Async database session
    """
    async with async_session_maker() as session:
        yield session
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd backend && python -m pytest tests/units/test_database_engine.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/core/database.py backend/tests/units/test_database_engine.py
git commit -m "feat(database): 将数据库引擎从 SQLite 切换到 PostgreSQL"
```

---

### Task 5: 更新 Alembic 配置

**Files:**
- Modify: `backend/alembic.ini`
- Modify: `backend/alembic/env.py`
- Delete: `backend/alembic/versions/001_create_initial_tables.py`
- Delete: `backend/alembic/versions/002_create_student_memories_table.py`
- Delete: `backend/alembic/versions/003_create_checkpoint_plans_table.py`
- Delete: `backend/alembic/versions/004_add_receiver_to_messages.py`

- [ ] **Step 1: 更新 alembic.ini**

将 `sqlalchemy.url` 更新为 PostgreSQL 同步驱动 URL：

```ini
sqlalchemy.url = postgresql+psycopg2://admin:123456@localhost:5432/mydb
```

只修改这一行，其余内容保持不变。

- [ ] **Step 2: 更新 alembic/env.py**

将 `backend/alembic/env.py` 替换为：

```python
"""Alembic 环境配置."""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config

from alembic import context

# 添加项目根目录到 Python 路径
sys_path = str(Path(__file__).resolve().parents[1])
if sys_path not in sys.path:
    sys.path.append(sys_path)

# 导入 ORM Base 和所有模型
# noqa: E402 - 导入必须在 sys.path.append() 之后，这是 Alembic env.py 的特殊情况
from core.database import Base  # noqa: E402

# this is the Alembic Config object
config = context.config

# 将 async URL 转换为同步 URL（用于 Alembic migrations）
# postgresql+asyncpg:// → postgresql+psycopg2://
database_url = config.get_main_option("sqlalchemy.url")
if database_url and "asyncpg" in database_url:
    database_url = database_url.replace("+asyncpg", "+psycopg2")
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

变更说明：
- URL 转换：`aiosqlite→sqlite` 改为 `asyncpg→psycopg2`
- 移除 `poolclass=pool.NullPool`，使用默认 `QueuePool`（PostgreSQL 支持连接池）

- [ ] **Step 3: 删除旧迁移文件**

```bash
cd backend
rm alembic/versions/001_create_initial_tables.py
rm alembic/versions/002_create_student_memories_table.py
rm alembic/versions/003_create_checkpoint_plans_table.py
rm alembic/versions/004_add_receiver_to_messages.py
```

- [ ] **Step 4: 生成全新基线迁移**

```bash
cd backend
alembic revision --autogenerate -m "initial_postgresql_schema"
```

Expected: 在 `alembic/versions/` 下生成新的迁移文件

- [ ] **Step 5: 验证迁移内容**

检查生成的迁移文件，确认：
- 包含所有 6 个表的 `op.create_table`
- `teaching_sessions` 表的 `students_config` 列使用 `sa.JSON()`（不是 `sa.Text()`）
- `student_memories` 表的 `level` 和 `attitude` 列使用 `sa.Enum()`
- 外键约束正确

- [ ] **Step 6: 执行迁移验证**

```bash
cd backend
alembic upgrade head
```

Expected: 迁移成功，PostgreSQL 中创建了所有表

- [ ] **Step 7: 验证回滚**

```bash
cd backend
alembic downgrade base
alembic upgrade head
```

Expected: downgrade 和 upgrade 均成功

- [ ] **Step 8: Commit**

```bash
git add backend/alembic.ini backend/alembic/env.py backend/alembic/versions/
git commit -m "feat(migration): 重置 Alembic 迁移为 PostgreSQL 基线"
```

---

### Task 6: 清理 conftest.py 中的 SQLite 特定代码

**Files:**
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: 编写 FK 回归测试**

创建 `backend/tests/units/test_foreign_key_enforcement.py`：

```python
"""测试外键约束在移除 PRAGMA 后仍然生效."""

import pytest


class TestForeignKeyEnforcement:
    """验证 SQLAlchemy inspect() 能正确识别外键约束定义.

    注意：SQLite 的外键约束在 ORM 层面通过 ForeignKey 定义即可被
    SQLAlchemy inspect() 检测到，无需 PRAGMA foreign_keys = ON。
    """

    @pytest.mark.asyncio
    async def test_messages_fk_detected_by_inspect(self, test_engine):
        """测试 messages 表的外键约束通过 SQLAlchemy inspect() 可检测."""
        from sqlalchemy import inspect

        engine, _ = test_engine
        inspector = inspect(engine)

        fks = inspector.get_foreign_keys("messages")
        assert len(fks) >= 1, "messages 表应该有外键约束"

        fk_refs = {(fk["referred_table"], tuple(fk["constrained_columns"])) for fk in fks}
        assert ("teaching_sessions", ("session_id",)) in fk_refs, (
            "messages.session_id 应该引用 teaching_sessions.id"
        )

    @pytest.mark.asyncio
    async def test_all_tables_with_fk_have_constraints_detected(self, test_engine):
        """测试所有包含外键的表都能通过 inspect() 检测到约束."""
        from sqlalchemy import inspect

        engine, _ = test_engine
        inspector = inspect(engine)

        tables_with_fk = {
            "messages": [("teaching_sessions", ("session_id",))],
            "session_memories": [("teaching_sessions", ("session_id",))],
            "teacher_memories": [("teaching_sessions", ("session_id",))],
            "student_memories": [("teaching_sessions", ("session_id",))],
        }

        for table, expected_refs in tables_with_fk.items():
            fks = inspector.get_foreign_keys(table)
            fk_refs = {(fk["referred_table"], tuple(fk["constrained_columns"])) for fk in fks}
            for ref_table, ref_cols in expected_refs:
                assert (ref_table, ref_cols) in fk_refs, (
                    f"{table} 缺少外键: {ref_table}({ref_cols})"
                )
```

- [ ] **Step 2: 运行 FK 测试确认当前行为**

Run: `cd backend && python -m pytest tests/units/test_foreign_key_enforcement.py -v`
Expected: PASS（当前有 PRAGMA 保护，测试应该通过）

- [ ] **Step 3: 清理 conftest.py**

将 `backend/tests/conftest.py` 替换为：

```python
"""Pytest configuration and fixtures."""

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

# 在任何 database 模块导入之前设置测试数据库 URL
# pytest 在加载测试模块之前会先加载 conftest.py
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config: pytest.Config) -> None:
    """注册自定义 marker."""
    config.addinivalue_line("markers", "integration: 真实 LLM API 集成测试（需要网络和 API key）")

    # 配置日志输出到文件
    import logging
    from pathlib import Path

    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    # 配置 root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.FileHandler(logs_dir / "tests.log"), logging.StreamHandler(sys.stdout)],
        force=True,  # 强制重新配置
    )


# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


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

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine, Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    engine, base = test_engine
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_engine_file():
    """Create test database engine using file database for tests that need cross-connection data sharing.

    This is required for tests using ASGITransport, which creates a separate database connection
    for each HTTP request. File database allows data to be shared across connections.
    """
    import tempfile
    from core.database import Base

    # Import all ORM models so they register with Base.metadata
    from orm.checkpoint_plan import CheckpointPlanModel  # noqa: F401
    from orm.message import MessageModel  # noqa: F401
    from orm.session_memory import SessionMemoryModel  # noqa: F401
    from orm.student_memory import StudentMemoryModel  # noqa: F401
    from orm.teacher_memory import TeacherMemoryModel  # noqa: F401
    from orm.teaching_session import TeachingSessionModel  # noqa: F401

    # Create a temporary file database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    # File database URL
    test_database_url = f"sqlite+aiosqlite:///{tmp_path}"

    engine = create_async_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine, Base, tmp_path, test_database_url

    # Cleanup: drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Delete the temporary file
    import contextlib
    import os
    with contextlib.suppress(OSError):
        os.unlink(tmp_path)


@pytest_asyncio.fixture(scope="function")
async def db_session_file(test_engine_file) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session using file database.

    Use this fixture for tests that need data to be visible across database connections,
    such as tests using ASGITransport for HTTP requests.
    """
    engine, base, tmp_path, test_database_url = test_engine_file
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture
def mock_llm_with_structured_output():
    """Mock LLM that supports structured output."""
    from unittest.mock import AsyncMock, MagicMock

    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_without_structured_output():
    """Mock LLM that doesn't support structured output."""
    from unittest.mock import AsyncMock, MagicMock

    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    return mock


@pytest.fixture
def mock_llm_json_parse_fails():
    """Mock LLM where both structured output and JSON parsing fail."""
    from unittest.mock import AsyncMock, MagicMock

    mock = MagicMock()
    mock.ainvoke = AsyncMock()
    return mock
```

移除内容：
- `import tempfile`（顶层，移到 `test_engine_file` 内部）
- `create_connection()` 死代码函数
- `import sqlite3`（在 `create_connection` 内部）
- `from sqlalchemy import event`（在 `test_engine` 内部）
- 两个 `enable_fk` event listener

- [ ] **Step 4: 运行所有现有测试验证无回归**

Run: `cd backend && python -m pytest tests/units/ -v --tb=short`
Expected: 所有单元测试通过

- [ ] **Step 5: 运行 FK 回归测试**

Run: `cd backend && python -m pytest tests/units/test_foreign_key_enforcement.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/tests/conftest.py backend/tests/units/test_foreign_key_enforcement.py
git commit -m "test(conftest): 移除 SQLite 特定代码，添加 FK 回归测试"
```

---

### Task 7: 重写 test_alembic_migration.py

**Files:**
- Modify: `backend/tests/integration/test_alembic_migration.py`

- [ ] **Step 1: 重写测试文件**

将 `backend/tests/integration/test_alembic_migration.py` 替换为：

```python
"""数据库表结构验证测试.

使用 SQLAlchemy inspect() 验证 ORM 模型产生的表结构正确性。
这些测试通过 Base.metadata.create_all 创建表（不运行 Alembic 迁移），
验证 ORM 模型定义的正确性。

Alembic 迁移的正确性通过 Task 5 的手动验证步骤（upgrade/downgrade）保证。
"""

from sqlalchemy import inspect as sa_inspect

import pytest


class TestTableStructure:
    """使用 SQLAlchemy inspect() 检查表结构（数据库无关）."""

    @pytest.mark.asyncio
    async def test_all_tables_exist(self, db_session):
        """测试所有 6 个表 + alembic_version 表已创建."""
        inspector = sa_inspect(db_session.bind)
        tables = inspector.get_table_names()
        expected_tables = {
            "teaching_sessions",
            "messages",
            "session_memories",
            "teacher_memories",
            "student_memories",
            "checkpoint_plans",
        }
        for table in expected_tables:
            assert table in tables, f"缺少表: {table}"

    @pytest.mark.asyncio
    async def test_teaching_sessions_columns(self, db_session):
        """测试 teaching_sessions 表包含所有必需列."""
        inspector = sa_inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("teaching_sessions")}
        expected_columns = {
            "id",
            "teaching_mode",
            "topic",
            "students_config",
            "duration_seconds",
            "status",
            "start_time",
            "end_time",
        }
        for col in expected_columns:
            assert col in columns, f"teaching_sessions 缺少列: {col}"

    @pytest.mark.asyncio
    async def test_messages_columns(self, db_session):
        """测试 messages 表包含所有必需列."""
        inspector = sa_inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("messages")}
        expected_columns = {
            "id",
            "session_id",
            "sender",
            "message_type",
            "content",
            "receiver",
            "timestamp",
        }
        for col in expected_columns:
            assert col in columns, f"messages 缺少列: {col}"

    @pytest.mark.asyncio
    async def test_session_memories_columns(self, db_session):
        """测试 session_memories 表包含所有必需列."""
        inspector = sa_inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("session_memories")}
        expected_columns = {
            "id",
            "session_id",
            "message_history",
            "teaching_summary",
            "last_updated",
        }
        for col in expected_columns:
            assert col in columns, f"session_memories 缺少列: {col}"

    @pytest.mark.asyncio
    async def test_teacher_memories_columns(self, db_session):
        """测试 teacher_memories 表包含所有必需列."""
        inspector = sa_inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("teacher_memories")}
        expected_columns = {
            "id",
            "session_id",
            "covered_topics",
            "student_questions",
            "student_participation",
            "teaching_progress",
            "student_misconceptions",
        }
        for col in expected_columns:
            assert col in columns, f"teacher_memories 缺少列: {col}"

    @pytest.mark.asyncio
    async def test_student_memories_columns(self, db_session):
        """测试 student_memories 表包含所有必需列."""
        inspector = sa_inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("student_memories")}
        expected_columns = {
            "id",
            "session_id",
            "student_name",
            "level",
            "attitude",
            "learning_ability",
            "learned_concepts",
            "confused_points",
            "questions_asked",
            "initial_knowledge_level",
            "current_knowledge_level",
            "learning_rate",
            "last_updated",
        }
        for col in expected_columns:
            assert col in columns, f"student_memories 缺少列: {col}"

    @pytest.mark.asyncio
    async def test_checkpoint_plans_columns(self, db_session):
        """测试 checkpoint_plans 表包含所有必需列."""
        inspector = sa_inspect(db_session.bind)
        columns = {c["name"] for c in inspector.get_columns("checkpoint_plans")}
        expected_columns = {
            "id",
            "session_id",
            "plan_data",
        }
        for col in expected_columns:
            assert col in columns, f"checkpoint_plans 缺少列: {col}"

    @pytest.mark.asyncio
    async def test_foreign_keys_exist(self, db_session):
        """测试外键约束存在."""
        inspector = sa_inspect(db_session.bind)

        # messages → teaching_sessions
        fks = inspector.get_foreign_keys("messages")
        fk_refs = {(fk["referred_table"], tuple(fk["constrained_columns"])) for fk in fks}
        assert ("teaching_sessions", ("session_id",)) in fk_refs

        # session_memories → teaching_sessions
        fks = inspector.get_foreign_keys("session_memories")
        fk_refs = {(fk["referred_table"], tuple(fk["constrained_columns"])) for fk in fks}
        assert ("teaching_sessions", ("session_id",)) in fk_refs

        # teacher_memories → teaching_sessions
        fks = inspector.get_foreign_keys("teacher_memories")
        fk_refs = {(fk["referred_table"], tuple(fk["constrained_columns"])) for fk in fks}
        assert ("teaching_sessions", ("session_id",)) in fk_refs

        # student_memories → teaching_sessions
        fks = inspector.get_foreign_keys("student_memories")
        fk_refs = {(fk["referred_table"], tuple(fk["constrained_columns"])) for fk in fks}
        assert ("teaching_sessions", ("session_id",)) in fk_refs


class TestPostgreSQLMigration:
    """可选：PostgreSQL 集成测试（需要 TEST_POSTGRESQL_URL 环境变量）.

    运行方式:
        TEST_POSTGRESQL_URL=postgresql+asyncpg://admin:123456@localhost:5432/mydb \
        pytest tests/integration/test_alembic_migration.py::TestPostgreSQLMigration -v
    """

    @pytest.fixture(autouse=True)
    def _skip_without_postgres(self):
        import os

        if not os.getenv("TEST_POSTGRESQL_URL"):
            pytest.skip("TEST_POSTGRESQL_URL not set")

    @pytest.mark.asyncio
    async def test_create_all_tables_on_postgresql(self):
        """验证 Base.metadata.create_all 在 PostgreSQL 上成功创建所有表."""
        import os

        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from core.database import Base

        # Import all ORM models
        from orm.checkpoint_plan import CheckpointPlanModel  # noqa: F401
        from orm.message import MessageModel  # noqa: F401
        from orm.session_memory import SessionMemoryModel  # noqa: F401
        from orm.student_memory import StudentMemoryModel  # noqa: F401
        from orm.teacher_memory import TeacherMemoryModel  # noqa: F401
        from orm.teaching_session import TeachingSessionModel  # noqa: F401

        url = os.environ["TEST_POSTGRESQL_URL"]
        engine = create_async_engine(url)

        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # 验证所有表存在
            inspector = sa_inspect(engine)
            tables = set(inspector.get_table_names())
            assert "teaching_sessions" in tables
            assert "messages" in tables
            assert "student_memories" in tables

            # 验证 JSON 列在 PostgreSQL 中是 JSONB 类型
            teaching_cols = {c["name"]: c["type"].__class__.__name__ for c in inspector.get_columns("teaching_sessions")}
            assert teaching_cols["students_config"] == "JSONB"

            # 验证 Enum 列在 PostgreSQL 中是 ENUM 类型
            student_cols = {c["name"]: c["type"].__class__.__name__ for c in inspector.get_columns("student_memories")}
            assert student_cols["level"] == "ENUM"
            assert student_cols["attitude"] == "ENUM"
        finally:
            # 清理：即使测试失败也确保表被删除
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
            except Exception:
                pass
            await engine.dispose()
```

- [ ] **Step 2: 运行测试验证通过（SQLite 部分）**

Run: `cd backend && python -m pytest tests/integration/test_alembic_migration.py::TestTableStructure -v`
Expected: 所有 TestTableStructure 测试通过

- [ ] **Step 3: 运行 PostgreSQL 集成测试（可选）**

```bash
cd backend
TEST_POSTGRESQL_URL=postgresql+asyncpg://admin:123456@localhost:5432/mydb \
python -m pytest tests/integration/test_alembic_migration.py::TestPostgreSQLMigration -v
```

Expected: 测试通过，验证 PostgreSQL 中 JSON 列为 JSONB、Enum 列为 ENUM

- [ ] **Step 4: Commit**

```bash
git add backend/tests/integration/test_alembic_migration.py
git commit -m "test(migration): 使用 SQLAlchemy inspect() 重写迁移测试，添加 PostgreSQL 集成测试"
```

---

### Task 8: 全量测试验证

**Files:** 无新文件修改

- [ ] **Step 1: 运行所有单元测试**

Run: `cd backend && python -m pytest tests/units/ -v --tb=short`
Expected: 所有单元测试通过

- [ ] **Step 2: 运行所有集成测试（不含 LLM）**

Run: `cd backend && python -m pytest tests/integration/ -v --tb=short`
Expected: 所有集成测试通过

- [ ] **Step 3: Ruff 代码检查**

Run: `cd backend && ruff check core/ alembic/ tests/ && ruff format --check core/ alembic/ tests/`
Expected: 无报错

- [ ] **Step 4: 手动验证 PostgreSQL 连接**

```bash
cd backend
alembic current
alembic history
```

Expected: 显示当前迁移版本和历史记录

- [ ] **Step 5: 最终 Commit（如有代码格式修复）**

```bash
git add -A
git commit -m "chore: 代码格式化"
```

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 2 | CLEAR | 3 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**VERDICT:** ENG CLEARED — ready to implement
