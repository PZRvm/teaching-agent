"""测试 database.py 引擎配置."""

import os
import sys

import pytest


def _clear_and_reload_database(url: str):
    """清除 core.settings 和 core.database 模块缓存，设置 DATABASE_URL 后重新加载.

    Args:
        url: 要设置的 DATABASE_URL 值

    Returns:
        重新加载后的 database 模块

    Raises:
        ValueError: 当 url 为空字符串时（database.py 的 guard）
    """
    os.environ["DATABASE_URL"] = url

    # 清除模块缓存（包括 core 包的 __dict__ 缓存）
    for mod in ("core.settings", "core.database"):
        sys.modules.pop(mod, None)
    core = sys.modules.get("core")
    if core and hasattr(core, "__dict__"):
        core.__dict__.pop("settings", None)
        core.__dict__.pop("database", None)

    from core import database

    return database


class TestDatabaseEngine:
    """测试数据库引擎配置."""

    def test_engine_uses_settings_url(self):
        """测试引擎使用 settings.DATABASE_URL."""
        database = _clear_and_reload_database("postgresql+asyncpg://test:123@localhost/testdb")

        try:
            assert database.async_engine.url.database == "testdb"
            assert database.async_engine.url.drivername == "postgresql+asyncpg"
        finally:
            import asyncio

            asyncio.run(database.async_engine.dispose())

    def test_no_check_same_thread(self):
        """测试 PostgreSQL 引擎不包含 SQLite 特定的 connect_args."""
        database = _clear_and_reload_database("postgresql+asyncpg://test:123@localhost/testdb")

        try:
            # PostgreSQL 不需要 check_same_thread 参数
            assert "check_same_thread" not in str(database.async_engine.url)
        finally:
            import asyncio

            asyncio.run(database.async_engine.dispose())

    def test_empty_database_url_raises_error(self):
        """测试空 DATABASE_URL 抛出 ValueError."""
        with pytest.raises(ValueError, match="DATABASE_URL"):
            _clear_and_reload_database("")

    def teardown_class(self):
        """测试类结束后恢复默认状态."""
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
        for mod in ("core.settings", "core.database"):
            sys.modules.pop(mod, None)
