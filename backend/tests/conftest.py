"""Pytest configuration and fixtures."""

import asyncio
import sys
import tempfile
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

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


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


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

    # Enable foreign key support in SQLite for cascade delete tests
    def create_connection():
        """Create a connection with foreign keys enabled."""
        import sqlite3

        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    from sqlalchemy import event

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable FK for each new connection
    def enable_fk(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    event.listen(engine.sync_engine, "connect", enable_fk)

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

    # Enable FK for each new connection
    from sqlalchemy import event

    def enable_fk(dbapi_conn, connection_record):
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    event.listen(engine.sync_engine, "connect", enable_fk)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine, Base, tmp_path, test_database_url

    # Cleanup: drop all tables and dispose engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

    # Delete the temporary file
    import os
    try:
        os.unlink(tmp_path)
    except OSError:
        pass


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
