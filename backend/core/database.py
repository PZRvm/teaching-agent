"""Database connection and session management."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.settings import DATABASE_MAX_OVERFLOW, DATABASE_POOL_SIZE, DATABASE_URL

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
