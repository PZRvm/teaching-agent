"""Alembic 迁移测试 - 验证 PostgreSQL 迁移文件结构与 ORM 模型一致."""

from pathlib import Path

import pytest


def _find_initial_migration(versions_dir: Path) -> Path:
    """找到初始迁移文件（down_revision 为 None 的文件）."""
    for migration in sorted(versions_dir.glob("*.py")):
        content = migration.read_text()
        # 初始迁移的 down_revision 为 None
        if "down_revision: str | Sequence[str] | None = None" in content:
            return migration
        # 兼容旧格式
        if "down_revision = None" in content:
            return migration
    raise FileNotFoundError("未找到初始迁移文件（down_revision 为 None）")


class TestAlembicMigrationFile:
    """验证 Alembic 迁移文件存在且包含正确的表定义."""

    @pytest.fixture
    def migration_path(self):
        """获取初始迁移文件路径."""
        versions_dir = Path(__file__).parents[2] / "alembic" / "versions"
        return _find_initial_migration(versions_dir)

    def test_migration_file_exists(self, migration_path):
        """测试迁移文件存在."""
        assert migration_path.exists()

    def test_migration_has_revision_id(self, migration_path):
        """测试迁移文件包含 revision ID."""
        content = migration_path.read_text()
        assert 'revision: str' in content
        assert 'down_revision' in content

    def test_migration_creates_all_tables(self, migration_path):
        """测试 upgrade 函数创建了所有预期的表."""
        content = migration_path.read_text()

        expected_tables = [
            "teaching_sessions",
            "messages",
            "session_memories",
            "teacher_memories",
            "student_memories",
            "checkpoint_plans",
        ]

        for table in expected_tables:
            assert f"op.create_table('{table}'" in content, (
                f"迁移文件中缺少 op.create_table('{table}')"
            )

    def test_migration_has_foreign_keys(self, migration_path):
        """测试迁移文件包含外键约束."""
        content = migration_path.read_text()

        # messages 表 → teaching_sessions
        assert "ForeignKeyConstraint(['session_id'], ['teaching_sessions.id']" in content

    def test_migration_downgrade_drops_all_tables(self, migration_path):
        """测试 downgrade 函数删除了所有表."""
        content = migration_path.read_text()

        expected_drops = [
            "teacher_memories",
            "student_memories",
            "session_memories",
            "messages",
            "teaching_sessions",
            "checkpoint_plans",
        ]

        for table in expected_drops:
            assert f"op.drop_table('{table}')" in content, (
                f"迁移文件中缺少 op.drop_table('{table}')"
            )

    def test_migration_downgrade_drops_enum_types(self, migration_path):
        """测试 downgrade 函数清理 PostgreSQL ENUM 类型."""
        content = migration_path.read_text()

        assert "DROP TYPE IF EXISTS studentlevel" in content
        assert "DROP TYPE IF EXISTS studentattitude" in content


class TestMigrationMatchesORM:
    """验证迁移文件中的表定义与 ORM 模型一致."""

    def test_all_orm_tables_covered_by_migration(self, test_engine):
        """测试 ORM 中定义的所有表都在迁移中创建."""
        from pathlib import Path

        _, base = test_engine
        orm_tables = set(base.metadata.tables.keys())

        versions_dir = Path(__file__).parents[2] / "alembic" / "versions"
        migration_path = _find_initial_migration(versions_dir)
        content = migration_path.read_text()

        for table_name in orm_tables:
            assert f"op.create_table('{table_name}'" in content, (
                f"ORM 定义了 {table_name} 表，但迁移文件中未创建"
            )
