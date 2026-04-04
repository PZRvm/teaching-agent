"""MemoryPersistence 测试."""

from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import (
    SessionMemory,
    TeacherAgentMemory,
)
from orm.teaching_session import TeachingSessionModel


@pytest.mark.asyncio
async def _create_teaching_session(db: AsyncSession) -> int:
    """辅助方法：创建教学会话."""
    session = TeachingSessionModel(
        teaching_mode="didactic",
        topic="Python基础",
        students_config={"students": []},
        status="running",
        start_time=datetime.now(),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session.id


@pytest.mark.asyncio
class TestMemoryPersistenceSave:
    """MemoryPersistence 保存操作测试."""

    async def test_save_session_memory_create(self, db_session: AsyncSession):
        """测试首次保存会话记忆（创建）."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)

        memory = SessionMemory(
            session_id=session_id,
            topic="Python基础",
            teaching_summary="已讲授变量",
        )

        persistence = MemoryPersistence(db_session)
        await persistence.save_session_memory(memory)

        from sqlalchemy import select

        from orm.session_memory import SessionMemoryModel

        result = await db_session.execute(
            select(SessionMemoryModel).where(
                SessionMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record is not None
        assert record.teaching_summary == "已讲授变量"
        assert record.message_history == []

    async def test_save_session_memory_update(self, db_session: AsyncSession):
        """测试更新已有的会话记忆."""
        from sqlalchemy import select

        from agents.memories.memory_persistence import MemoryPersistence
        from orm.session_memory import SessionMemoryModel

        session_id = await _create_teaching_session(db_session)

        # 第一次保存
        persistence = MemoryPersistence(db_session)
        memory = SessionMemory(session_id=session_id, topic="Python基础")
        await persistence.save_session_memory(memory)

        # 第二次保存（更新）
        memory.teaching_summary = "已讲授变量和数据类型"
        await persistence.save_session_memory(memory)

        result = await db_session.execute(
            select(SessionMemoryModel).where(
                SessionMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record.teaching_summary == "已讲授变量和数据类型"

    async def test_save_teacher_memory_create(self, db_session: AsyncSession):
        """测试首次保存教师记忆."""
        from sqlalchemy import select

        from agents.memories.memory_persistence import MemoryPersistence
        from orm.teacher_memory import TeacherMemoryModel

        session_id = await _create_teaching_session(db_session)

        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("变量")
        teacher_mem.record_student_participation("张三")

        persistence = MemoryPersistence(db_session)
        await persistence.save_teacher_memory(session_id, teacher_mem)

        result = await db_session.execute(
            select(TeacherMemoryModel).where(
                TeacherMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record is not None
        assert "变量" in record.covered_topics
        assert record.student_participation == {"张三": 1}

    async def test_save_teacher_memory_update(self, db_session: AsyncSession):
        """测试更新已有的教师记忆."""
        from sqlalchemy import select

        from agents.memories.memory_persistence import MemoryPersistence
        from orm.teacher_memory import TeacherMemoryModel

        session_id = await _create_teaching_session(db_session)

        persistence = MemoryPersistence(db_session)

        # 第一次保存
        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("变量")
        await persistence.save_teacher_memory(session_id, teacher_mem)

        # 第二次保存（更新）
        teacher_mem.record_covered_topic("函数")
        await persistence.save_teacher_memory(session_id, teacher_mem)

        result = await db_session.execute(
            select(TeacherMemoryModel).where(
                TeacherMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert "变量" in record.covered_topics
        assert "函数" in record.covered_topics

    async def test_save_student_memory_create(self, db_session: AsyncSession):
        """测试首次保存学生记忆."""
        from sqlalchemy import select

        from agents.memories.memory_manager import StudentAgentMemory
        from agents.memories.memory_persistence import MemoryPersistence
        from orm.student_memory import StudentMemoryModel
        from schemas.student import StudentLevel, StudentProfile

        session_id = await _create_teaching_session(db_session)

        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(
                name="张三",
                level=StudentLevel.EXCELLENT,
                learning_ability=8,
            )
        )
        student_mem.learned_concepts.append("变量")

        persistence = MemoryPersistence(db_session)
        await persistence.save_student_memory(session_id, student_mem)

        result = await db_session.execute(
            select(StudentMemoryModel).where(
                StudentMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert record is not None
        assert record.student_name == "张三"
        assert "变量" in record.learned_concepts

    async def test_save_student_memory_update(self, db_session: AsyncSession):
        """测试更新已有的学生记忆."""
        from sqlalchemy import select

        from agents.memories.memory_manager import StudentAgentMemory
        from agents.memories.memory_persistence import MemoryPersistence
        from orm.student_memory import StudentMemoryModel
        from schemas.student import StudentProfile

        session_id = await _create_teaching_session(db_session)

        persistence = MemoryPersistence(db_session)

        # 第一次保存
        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(name="张三", learning_ability=8)
        )
        # 先添加一个概念，验证更新能正确保存多个概念
        student_mem.learned_concepts.append("变量")
        await persistence.save_student_memory(session_id, student_mem)

        # 第二次保存（更新）
        student_mem.learned_concepts.append("函数")
        student_mem.current_knowledge_level = 0.3
        await persistence.save_student_memory(session_id, student_mem)

        result = await db_session.execute(
            select(StudentMemoryModel).where(
                StudentMemoryModel.session_id == session_id
            )
        )
        record = result.scalar_one()
        assert "变量" in record.learned_concepts
        assert "函数" in record.learned_concepts
        assert record.current_knowledge_level == 0.3

    async def test_save_message(self, db_session: AsyncSession):
        """测试保存单条消息."""
        from sqlalchemy import select

        from agents.memories.memory_persistence import MemoryPersistence
        from orm.message import MessageModel
        from schemas.message import Message, MessageType

        session_id = await _create_teaching_session(db_session)

        msg = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="今天学习变量",
            timestamp=datetime.now(),
        )

        persistence = MemoryPersistence(db_session)
        await persistence.save_message(session_id, msg)

        result = await db_session.execute(
            select(MessageModel).where(MessageModel.session_id == session_id)
        )
        records = result.scalars().all()
        assert len(records) == 1
        assert records[0].sender == "teacher"
        assert records[0].content == "今天学习变量"
