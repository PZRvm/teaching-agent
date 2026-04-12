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

from orm.checkpoint_plan import CheckpointPlanModel  # noqa: E401, F401
from orm.message import MessageModel  # noqa: E401, F401
from orm.session_memory import SessionMemoryModel  # noqa: E401, F401
from orm.student_memory import StudentMemoryModel  # noqa: E401, F401
from orm.teacher_memory import TeacherMemoryModel  # noqa: E401, F401
from orm.teaching_session import TeachingSessionModel  # noqa: E401, F401

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
