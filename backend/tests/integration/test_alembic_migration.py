"""Alembic 迁移测试 - 验证数据库表结构正确创建."""

import sqlite3
from pathlib import Path

import pytest


class TestAlembicMigration:
    """测试 Alembic 迁移是否正确执行."""

    @pytest.fixture
    def db_path(self):
        """获取数据库文件路径."""
        return Path(__file__).parents[2] / "datas" / "database.db"

    def test_database_file_exists(self, db_path):
        """测试数据库文件是否存在."""
        assert db_path.exists(), "数据库文件不存在，请先运行 alembic upgrade head"

    def test_all_tables_exist(self, db_path):
        """测试所有表是否已创建."""
        if not db_path.exists():
            pytest.skip("数据库文件不存在，跳过表检查")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        conn.close()

        expected_tables = {
            "teaching_sessions",
            "session_memories",
            "teacher_memories",
            "messages",
            "alembic_version",
        }

        missing_tables = expected_tables - tables
        assert not missing_tables, f"缺少表: {missing_tables}"

    def test_teaching_sessions_structure(self, db_path):
        """测试 teaching_sessions 表结构是否正确."""
        if not db_path.exists():
            pytest.skip("数据库文件不存在，跳过结构检查")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(teaching_sessions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        conn.close()

        # 验证必需的列存在
        required_columns = {
            "id": "INTEGER",
            "teaching_mode": "VARCHAR",
            "topic": "VARCHAR",
            "students_config": "JSON",
            "duration_seconds": "INTEGER",
            "status": "VARCHAR",
            "start_time": "DATETIME",
            "end_time": "DATETIME",
        }

        for col_name, _expected_type in required_columns.items():
            assert col_name in columns, f"缺少列: {col_name}"

    def test_session_memories_structure(self, db_path):
        """测试 session_memories 表结构是否正确."""
        if not db_path.exists():
            pytest.skip("数据库文件不存在，跳过结构检查")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(session_memories)")
        columns = {row[1] for row in cursor.fetchall()}

        conn.close()

        required_columns = {
            "id",
            "session_id",
            "message_history",
            "teaching_summary",
            "last_updated",
        }
        for col_name in required_columns:
            assert col_name in columns, f"缺少列: {col_name}"

    def test_messages_structure(self, db_path):
        """测试 messages 表结构是否正确."""
        if not db_path.exists():
            pytest.skip("数据库文件不存在，跳过结构检查")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(messages)")
        columns = {row[1] for row in cursor.fetchall()}

        conn.close()

        required_columns = {"id", "session_id", "sender", "message_type", "content", "timestamp"}
        for col_name in required_columns:
            assert col_name in columns, f"缺少列: {col_name}"

    def test_teacher_memories_structure(self, db_path):
        """测试 teacher_memories 表结构是否正确."""
        if not db_path.exists():
            pytest.skip("数据库文件不存在，跳过结构检查")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(teacher_memories)")
        columns = {row[1] for row in cursor.fetchall()}

        conn.close()

        required_columns = {
            "id",
            "session_id",
            "covered_topics",
            "student_questions",
            "student_participation",
            "teaching_progress",
            "student_misconceptions",
        }
        for col_name in required_columns:
            assert col_name in columns, f"缺少列: {col_name}"

    def test_foreign_keys_exist_in_schema(self, db_path):
        """测试外键约束是否在 schema 中定义（SQLite 在连接时启用）."""
        if not db_path.exists():
            pytest.skip("数据库文件不存在，跳过外键检查")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 检查 session_memories 表的外键定义
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='session_memories'"
        )
        result = cursor.fetchone()
        schema_sql = result[0] if result else ""

        conn.close()

        # SQLite 的外键约束在 CREATE TABLE 语句中定义
        # 实际启用需要在每次连接时执行 PRAGMA foreign_keys = ON
        assert "FOREIGN KEY(session_id) REFERENCES teaching_sessions (id)" in schema_sql, (
            f"缺少外键约束定义。实际 schema: {schema_sql}"
        )
