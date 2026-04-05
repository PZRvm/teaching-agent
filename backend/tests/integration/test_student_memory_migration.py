"""测试 student_memories 表迁移."""

import pytest


@pytest.mark.asyncio
class TestStudentMemoryMigration:
    """测试 student_memories 表迁移."""

    async def test_student_memories_orm_model_exists(self):
        """测试 StudentMemoryModel ORM 模型是否可以导入."""
        from orm.student_memory import StudentMemoryModel  # noqa: F401

        assert StudentMemoryModel is not None
        assert StudentMemoryModel.__tablename__ == "student_memories"

    async def test_student_memories_model_has_required_fields(self):
        """测试 StudentMemoryModel 是否包含所有必需的字段."""
        from orm.student_memory import StudentMemoryModel

        # 检查表名
        assert StudentMemoryModel.__tablename__ == "student_memories"

        # 检查列名（通过 __table__ 属性）
        column_names = {col.name for col in StudentMemoryModel.__table__.columns}

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
        assert column_names == expected_columns, (
            f"列不匹配: 期望 {expected_columns}, 实际 {column_names}"
        )

    async def test_student_memories_model_indexes(self):
        """测试 StudentMemoryModel 是否定义了索引."""
        from orm.student_memory import StudentMemoryModel

        index_names = {idx.name for idx in StudentMemoryModel.__table__.indexes}

        expected_indexes = {
            "ix_student_memories_session_id",
            "ix_student_memories_session_student",
        }
        assert expected_indexes.issubset(index_names), (
            f"索引不匹配: 期望包含 {expected_indexes}, 实际 {index_names}"
        )

    async def test_student_memories_foreign_key(self):
        """测试 StudentMemoryModel 外键是否正确."""
        # Import all models to ensure metadata is complete
        from orm.student_memory import StudentMemoryModel
        from orm.teaching_session import TeachingSessionModel  # noqa: F401

        # 获取 session_id 列的外键约束
        foreign_keys = list(StudentMemoryModel.__table__.foreign_keys)

        assert len(foreign_keys) == 1, f"期望 1 个外键, 实际 {len(foreign_keys)}"

        fk = foreign_keys[0]
        # 检查外键定义字符串
        assert "teaching_sessions.id" in str(fk.target_fullname)
