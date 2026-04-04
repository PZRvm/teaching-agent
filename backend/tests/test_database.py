"""Database layer tests.

These tests are written FIRST (TDD) - they will fail because ORM models don't exist yet.
"""

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestTeachingSessionModel:
    """Test TeachingSessionModel ORM operations."""

    @pytest.mark.asyncio
    async def test_create_teaching_session(self, db_session: AsyncSession) -> None:
        """Test creating a teaching session."""
        # Import the model (doesn't exist yet - will cause import error)

        from orm.teaching_session import TeachingSessionModel

        # Create a session
        session = TeachingSessionModel(
            teaching_mode="didactic",
            topic="Test Topic",
            students_config=[{"name": "Alice"}],
            duration_seconds=3600,
            status="running",
            start_time=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None
        assert session.teaching_mode == "didactic"
        assert session.topic == "Test Topic"
        assert session.status == "running"

    @pytest.mark.asyncio
    async def test_read_teaching_session(self, db_session: AsyncSession) -> None:
        """Test reading a teaching session."""
        from orm.teaching_session import TeachingSessionModel

        # Create
        session = TeachingSessionModel(
            teaching_mode="heuristic",
            topic="Another Topic",
            students_config=[{"name": "Bob"}],
            start_time=datetime.utcnow(),
        )
        db_session.add(session)
        await db_session.commit()

        # Read
        result = await db_session.execute(
            select(TeachingSessionModel).where(TeachingSessionModel.topic == "Another Topic")
        )
        found = result.scalar_one()

        assert found.teaching_mode == "heuristic"
        assert found.students_config == [{"name": "Bob"}]


class TestMessageModel:
    """Test MessageModel ORM operations."""

    @pytest.mark.asyncio
    async def test_create_message(self, db_session: AsyncSession) -> None:
        """Test creating a message."""
        from orm.message import MessageModel
        from orm.teaching_session import TeachingSessionModel

        # First create a session
        teaching_session = TeachingSessionModel(
            teaching_mode="didactic",
            topic="Test",
            students_config=[],
            start_time=datetime.utcnow(),
        )
        db_session.add(teaching_session)
        await db_session.commit()
        await db_session.refresh(teaching_session)

        # Create message
        message = MessageModel(
            session_id=teaching_session.id,
            sender="teacher",
            message_type="lecture",
            content="Hello class!",
            timestamp=datetime.utcnow(),
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        assert message.id is not None
        assert message.sender == "teacher"
        assert message.message_type == "lecture"
        assert message.content == "Hello class!"

    @pytest.mark.asyncio
    async def test_message_session_relationship(self, db_session: AsyncSession) -> None:
        """Test message-to-session relationship."""
        from orm.message import MessageModel
        from orm.teaching_session import TeachingSessionModel

        # Create session
        teaching_session = TeachingSessionModel(
            teaching_mode="discussion",
            topic="Discussion Topic",
            students_config=[],
            start_time=datetime.utcnow(),
        )
        db_session.add(teaching_session)
        await db_session.commit()

        # Create multiple messages
        for i in range(3):
            message = MessageModel(
                session_id=teaching_session.id,
                sender=f"student_{i}",
                message_type="question_to_teacher",
                content=f"Question {i}",
                timestamp=datetime.utcnow(),
            )
            db_session.add(message)
        await db_session.commit()

        # Query messages for this session
        result = await db_session.execute(
            select(MessageModel).where(MessageModel.session_id == teaching_session.id)
        )
        messages = result.scalars().all()

        assert len(messages) == 3


class TestSessionMemoryModel:
    """Test SessionMemoryModel ORM operations."""

    @pytest.mark.asyncio
    async def test_create_session_memory(self, db_session: AsyncSession) -> None:
        """Test creating session memory."""
        from orm.session_memory import SessionMemoryModel
        from orm.teaching_session import TeachingSessionModel

        # Create teaching session first
        teaching_session = TeachingSessionModel(
            teaching_mode="didactic",
            topic="Memory Test",
            students_config=[],
            start_time=datetime.utcnow(),
        )
        db_session.add(teaching_session)
        await db_session.commit()
        await db_session.refresh(teaching_session)

        # Create session memory
        memory = SessionMemoryModel(
            session_id=teaching_session.id,
            message_history=[{"sender": "teacher", "content": "Welcome"}],
            teaching_summary="First class",
            last_updated=datetime.utcnow(),
        )
        db_session.add(memory)
        await db_session.commit()
        await db_session.refresh(memory)

        assert memory.id is not None
        assert memory.teaching_summary == "First class"
        assert len(memory.message_history) == 1


class TestTeacherMemoryModel:
    """Test TeacherMemoryModel ORM operations."""

    @pytest.mark.asyncio
    async def test_create_teacher_memory(self, db_session: AsyncSession) -> None:
        """Test creating teacher memory."""
        from orm.teacher_memory import TeacherMemoryModel
        from orm.teaching_session import TeachingSessionModel

        # Create teaching session first
        teaching_session = TeachingSessionModel(
            teaching_mode="heuristic",
            topic="Teacher Memory Test",
            students_config=[],
            start_time=datetime.utcnow(),
        )
        db_session.add(teaching_session)
        await db_session.commit()
        await db_session.refresh(teaching_session)

        # Create teacher memory
        memory = TeacherMemoryModel(
            session_id=teaching_session.id,
            covered_topics=["Introduction", "Basics"],
            student_questions={"Alice": ["What is X?"]},
            student_participation={"Alice": 2, "Bob": 1},
            teaching_progress=0.3,
            student_misconceptions={},
        )
        db_session.add(memory)
        await db_session.commit()
        await db_session.refresh(memory)

        assert memory.id is not None
        assert memory.teaching_progress == 0.3
        assert len(memory.covered_topics) == 2
        assert memory.student_participation["Alice"] == 2
