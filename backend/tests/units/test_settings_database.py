"""测试 settings.py 数据库配置加载."""

import os
import sys
from unittest.mock import patch


class TestDatabaseSettings:
    """测试数据库配置从 YAML 和环境变量加载."""

    def test_database_url_attribute_exists(self):
        """测试 DATABASE_URL 属性存在."""
        from core import settings

        assert hasattr(settings, "DATABASE_URL")
        assert isinstance(settings.DATABASE_URL, str)

    def test_database_url_from_env(self):
        """测试 DATABASE_URL 环境变量覆盖 YAML 配置."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://test:123@localhost/testdb"}):
            # 清除缓存以强制重新加载
            sys.modules.pop("core.settings", None)
            core = sys.modules.get("core")
            if core and hasattr(core, "__dict__"):
                core.__dict__.pop("settings", None)

            from core import settings

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
