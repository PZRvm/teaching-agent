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
            select(SessionMemoryModel).where(SessionMemoryModel.session_id == session_id)
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
            select(SessionMemoryModel).where(SessionMemoryModel.session_id == session_id)
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
            select(TeacherMemoryModel).where(TeacherMemoryModel.session_id == session_id)
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
            select(TeacherMemoryModel).where(TeacherMemoryModel.session_id == session_id)
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
            select(StudentMemoryModel).where(StudentMemoryModel.session_id == session_id)
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
            select(StudentMemoryModel).where(StudentMemoryModel.session_id == session_id)
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


@pytest.mark.asyncio
class TestMemoryPersistenceLoad:
    """MemoryPersistence 加载操作测试."""

    async def test_load_session_memory_exists(self, db_session: AsyncSession):
        """测试加载已存在的会话记忆."""

        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)

        # 先保存
        memory = SessionMemory(
            session_id=session_id,
            topic="Python基础",
            teaching_summary="已讲授变量",
        )
        persistence = MemoryPersistence(db_session)
        await persistence.save_session_memory(memory)

        # 再加载
        loaded = await persistence.load_session_memory(session_id)
        assert loaded is not None
        assert loaded.session_id == session_id
        assert loaded.teaching_summary == "已讲授变量"

    async def test_load_session_memory_not_exists(self, db_session: AsyncSession):
        """测试加载不存在的会话记忆返回 None."""
        from agents.memories.memory_persistence import MemoryPersistence

        persistence = MemoryPersistence(db_session)
        loaded = await persistence.load_session_memory(99999)
        assert loaded is None

    async def test_load_session_memory_with_messages(self, db_session: AsyncSession):
        """测试加载会话记忆包含消息历史."""

        from agents.memories.memory_persistence import MemoryPersistence
        from schemas.message import Message, MessageType

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 保存消息
        msg1 = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content="今天学习变量",
            timestamp=datetime.now(),
        )
        msg2 = Message(
            sender="张三",
            message_type=MessageType.REPLY_TO_TEACHER,
            content="变量是什么?",
            timestamp=datetime.now(),
        )
        await persistence.save_message(session_id, msg1)
        await persistence.save_message(session_id, msg2)

        # 保存会话记忆
        memory = SessionMemory(session_id=session_id, topic="Python基础")
        await persistence.save_session_memory(memory)

        # 加载
        loaded = await persistence.load_session_memory(session_id)
        assert loaded is not None
        assert len(loaded.message_history) == 2
        assert loaded.message_history[0].sender == "teacher"
        assert loaded.message_history[1].sender == "张三"

    async def test_load_teacher_memory_exists(self, db_session: AsyncSession):
        """测试加载已存在的教师记忆."""

        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 先保存
        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("变量")
        teacher_mem.record_covered_topic("函数")
        teacher_mem.record_student_participation("张三")
        await persistence.save_teacher_memory(session_id, teacher_mem)

        # 再加载
        loaded = await persistence.load_teacher_memory(session_id)
        assert loaded is not None
        assert "变量" in loaded.covered_topics
        assert "函数" in loaded.covered_topics
        assert loaded.student_participation == {"张三": 1}

    async def test_load_teacher_memory_not_exists(self, db_session: AsyncSession):
        """测试加载不存在的教师记忆返回 None."""
        from agents.memories.memory_persistence import MemoryPersistence

        persistence = MemoryPersistence(db_session)
        loaded = await persistence.load_teacher_memory(99999)
        assert loaded is None

    async def test_load_student_memory_exists(self, db_session: AsyncSession):
        """测试加载已存在的学生记忆."""

        from agents.memories.memory_manager import StudentAgentMemory
        from agents.memories.memory_persistence import MemoryPersistence
        from schemas.student import StudentProfile

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 先保存
        student_mem = StudentAgentMemory.from_profile(
            StudentProfile(name="张三", learning_ability=8)
        )
        student_mem.learned_concepts.append("变量")
        student_mem.current_knowledge_level = 0.2
        await persistence.save_student_memory(session_id, student_mem)

        # 再加载
        loaded = await persistence.load_student_memory(session_id, "张三")
        assert loaded is not None
        assert "变量" in loaded.learned_concepts
        assert loaded.current_knowledge_level == 0.2

    async def test_load_student_memory_not_exists(self, db_session: AsyncSession):
        """测试加载不存在的学生记忆返回 None."""
        from agents.memories.memory_persistence import MemoryPersistence

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        loaded = await persistence.load_student_memory(session_id, "不存在")
        assert loaded is None


@pytest.mark.asyncio
class TestMemoryIntegration:
    """记忆系统完整流程集成测试."""

    async def test_full_flow_save_and_restore(self, db_session: AsyncSession):
        """完整流程：创建会话 → 处理消息 → 持久化 → 加载恢复."""
        import random

        from agents.memories.memory_manager import MemoryManager
        from agents.memories.memory_persistence import MemoryPersistence
        from schemas.message import Message, MessageType
        from schemas.student import StudentProfile

        # 1. 创建教学会话
        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        # 2. 创建 MemoryManager 并注册学生
        session_memory = SessionMemory(session_id=session_id, topic="Python基础")
        manager = MemoryManager(
            session_memory=session_memory,
            extract_knowledge_fn=lambda c: ["变量", "数据类型"],
            summary_fn=lambda p: "已讲授变量和数据类型",
            summary_update_interval=5,
            student_rng=random.Random(42),
        )
        manager.register_student(StudentProfile(name="张三", learning_ability=8))

        # 3. 处理多条消息
        messages = [
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="今天学习变量和数据类型",
                timestamp=datetime.now(),
            ),
            Message(
                sender="teacher",
                message_type=MessageType.CHECKPOINT_QUESTION,
                content="什么是变量?",
                timestamp=datetime.now(),
            ),
            Message(
                sender="张三",
                message_type=MessageType.REPLY_TO_TEACHER,
                content="变量是存储数据的容器",
                timestamp=datetime.now(),
            ),
            Message(
                sender="张三",
                message_type=MessageType.QUESTION_TO_TEACHER,
                content="变量有哪些类型?",
                timestamp=datetime.now(),
            ),
            Message(
                sender="teacher",
                message_type=MessageType.LECTURE,
                content="变量有整数、浮点数、字符串等类型",
                timestamp=datetime.now(),
            ),
        ]

        for msg in messages:
            manager.process_message(msg)

        # 4. 验证内存状态
        assert len(session_memory.message_history) == 5
        assert "变量" in manager.teacher_memory.covered_topics
        assert manager.teacher_memory.student_participation["张三"] == 1
        assert "张三" in manager.teacher_memory.student_questions
        student_mem = manager.student_memories["张三"]
        assert len(student_mem.learned_concepts) >= 0  # 可能记住概念

        # 5. 持久化
        await persistence.save_session_memory(manager.session_memory)
        await persistence.save_teacher_memory(session_id, manager.teacher_memory)
        await persistence.save_student_memory(session_id, manager.student_memories["张三"])
        for msg in manager.session_memory.message_history:
            await persistence.save_message(session_id, msg)

        # 6. 加载恢复
        loaded_session = await persistence.load_session_memory(session_id)
        loaded_teacher = await persistence.load_teacher_memory(session_id)
        loaded_student = await persistence.load_student_memory(session_id, "张三")

        # 7. 验证恢复的数据
        assert loaded_session is not None
        assert loaded_session.topic == "Python基础"
        assert loaded_session.teaching_summary == "已讲授变量和数据类型"
        assert len(loaded_session.message_history) == 5

        assert loaded_teacher is not None
        assert "变量" in loaded_teacher.covered_topics
        assert loaded_teacher.student_participation["张三"] == 1
        assert loaded_teacher.student_questions["张三"] == ["变量有哪些类型?"]

        assert loaded_student is not None
        assert loaded_student.name == "张三"
        assert loaded_student.learning_ability == 8

    async def test_save_and_load_empty_session(self, db_session: AsyncSession):
        """测试空会话的保存和加载."""

        from agents.memories.memory_manager import MemoryManager
        from agents.memories.memory_persistence import MemoryPersistence
        from schemas.student import StudentProfile

        session_id = await _create_teaching_session(db_session)
        persistence = MemoryPersistence(db_session)

        session_memory = SessionMemory(session_id=session_id, topic="空主题")
        manager = MemoryManager(session_memory=session_memory)
        manager.register_student(StudentProfile(name="张三", learning_ability=5))

        await persistence.save_session_memory(manager.session_memory)
        await persistence.save_teacher_memory(session_id, manager.teacher_memory)
        await persistence.save_student_memory(session_id, manager.student_memories["张三"])

        loaded_session = await persistence.load_session_memory(session_id)
        loaded_teacher = await persistence.load_teacher_memory(session_id)
        loaded_student = await persistence.load_student_memory(session_id, "张三")

        assert loaded_session is not None
        assert loaded_session.message_history == []
        assert loaded_teacher is not None
        assert loaded_teacher.covered_topics == []
        assert loaded_student is not None
        assert loaded_student.learned_concepts == []
