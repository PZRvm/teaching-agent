"""Database connection and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from typing import Any


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


def _create_engine_and_session() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """创建数据库引擎和会话工厂（延迟加载）.

    允许 Alembic env.py 导入 Base 而不触发引擎创建。
    首次访问 async_engine 或 async_session_maker 时才会执行。

    Returns:
        (异步引擎, 异步会话工厂) 元组
    """
    from core.settings import DATABASE_MAX_OVERFLOW, DATABASE_POOL_SIZE, DATABASE_URL

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL 未设置。请在 backend/.env 中配置 DATABASE_URL，"
            "例如: DATABASE_URL=postgresql+asyncpg://admin:123456@localhost:5432/mydb"
        )

    _engine_kwargs: dict[str, Any] = {"echo": False}
    if DATABASE_URL.startswith("postgresql"):
        _engine_kwargs["pool_size"] = DATABASE_POOL_SIZE
        _engine_kwargs["max_overflow"] = DATABASE_MAX_OVERFLOW
        _engine_kwargs["pool_pre_ping"] = True

    engine = create_async_engine(DATABASE_URL, **_engine_kwargs)
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_maker


# 模块级缓存（延迟初始化）
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def __getattr__(name: str) -> Any:
    """延迟初始化 async_engine 和 async_session_maker.

    当 Alembic env.py 仅导入 Base 时，不会触发引擎创建。
    只有在业务代码实际访问 async_engine 时才会创建连接。
    """
    global _engine, _session_maker

    if name == "async_engine":
        if _engine is None:
            _engine, _session_maker = _create_engine_and_session()
        return _engine

    if name == "async_session_maker":
        if _session_maker is None:
            _engine, _session_maker = _create_engine_and_session()
        return _session_maker

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting async database sessions.

    Yields:
        Async database session
    """
    import sys

    _db = sys.modules[__name__]
    async with _db.async_session_maker() as session:
        yield session
