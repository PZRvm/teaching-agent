"""记忆持久化服务 - 数据库 save/load 操作."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import (
    SessionMemory,
    StudentAgentMemory,
    TeacherAgentMemory,
)
from core.database import Base
from orm.message import MessageModel
from orm.session_memory import SessionMemoryModel
from orm.student_memory import StudentMemoryModel
from orm.teacher_memory import TeacherMemoryModel
from schemas.message import Message

T = TypeVar("T", bound=Base)


class MemoryPersistence:
    """记忆持久化服务."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化.

        Args:
            db_session: SQLAlchemy 异步会话
        """
        self.db_session = db_session

    async def _upsert(
        self,
        model: type[T],
        session_id: int,
        update_fn: Callable[[T], None],
        create_fn: Callable[[], dict[str, Any]],
    ) -> T:
        """通用的 upsert 操作.

        Args:
            model: ORM 模型类
            session_id: 会话ID
            update_fn: 更新现有记录的函数
            create_fn: 创建新记录的函数，返回字段字典

        Returns:
            ORM 模型实例
        """
        result = await self.db_session.execute(
            select(model).where(model.session_id == session_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            update_fn(existing)
            await self.db_session.commit()
            return existing

        db_record = model(**create_fn())
        self.db_session.add(db_record)
        await self.db_session.commit()
        return db_record

    async def save_session_memory(
        self, memory: SessionMemory
    ) -> SessionMemoryModel:
        """保存会话记忆到数据库.

        Args:
            memory: 会话记忆对象

        Returns:
            ORM 模型实例
        """
        def update_fn(existing: SessionMemoryModel) -> None:
            existing.teaching_summary = memory.teaching_summary
            existing.message_history = [
                m.model_dump(mode="json") for m in memory.message_history
            ]
            existing.last_updated = datetime.now()

        def create_fn() -> dict[str, Any]:
            return {
                "session_id": memory.session_id,
                "message_history": [
                    m.model_dump(mode="json") for m in memory.message_history
                ],
                "teaching_summary": memory.teaching_summary or None,
                "last_updated": datetime.now(),
            }

        return await self._upsert(
            SessionMemoryModel, memory.session_id, update_fn, create_fn
        )

    async def save_teacher_memory(
        self, session_id: int, teacher_memory: TeacherAgentMemory
    ) -> TeacherMemoryModel:
        """保存教师记忆.

        Args:
            session_id: 会话ID
            teacher_memory: 教师记忆对象

        Returns:
            ORM 模型实例
        """
        def update_fn(existing: TeacherMemoryModel) -> None:
            existing.covered_topics = teacher_memory.covered_topics
            existing.student_questions = teacher_memory.student_questions
            existing.teaching_progress = teacher_memory.teaching_progress
            existing.student_participation = teacher_memory.student_participation
            existing.student_misconceptions = teacher_memory.student_misconceptions

        def create_fn() -> dict[str, Any]:
            return {
                "session_id": session_id,
                "covered_topics": teacher_memory.covered_topics,
                "student_questions": teacher_memory.student_questions,
                "teaching_progress": teacher_memory.teaching_progress,
                "student_participation": teacher_memory.student_participation,
                "student_misconceptions": teacher_memory.student_misconceptions,
            }

        return await self._upsert(
            TeacherMemoryModel, session_id, update_fn, create_fn
        )

    async def save_message(self, session_id: int, message: Message) -> MessageModel:
        """保存单条消息到数据库.

        Args:
            session_id: 会话ID
            message: 消息对象

        Returns:
            ORM 模型实例
        """
        db_message = MessageModel(
            session_id=session_id,
            sender=message.sender,
            message_type=message.message_type.value,
            content=message.content,
            timestamp=message.timestamp or datetime.now(),
        )
        self.db_session.add(db_message)
        await self.db_session.commit()
        await self.db_session.refresh(db_message)
        return db_message

    async def save_student_memory(
        self, session_id: int, student_memory: StudentAgentMemory
    ) -> StudentMemoryModel:
        """保存学生记忆.

        Args:
            session_id: 会话ID
            student_memory: 学生记忆对象

        Returns:
            ORM 模型实例
        """
        def update_fn(existing: StudentMemoryModel) -> None:
            existing.learned_concepts = student_memory.learned_concepts
            existing.confused_points = student_memory.confused_points
            existing.questions_asked = student_memory.questions_asked
            existing.initial_knowledge_level = student_memory.initial_knowledge_level
            existing.current_knowledge_level = student_memory.current_knowledge_level
            existing.learning_rate = student_memory.learning_rate
            existing.last_updated = datetime.now()

        def create_fn() -> dict[str, Any]:
            return {
                "session_id": session_id,
                "student_name": student_memory.name,
                "level": student_memory.level.value,
                "attitude": student_memory.attitude.value,
                "learning_ability": student_memory.learning_ability,
                "learned_concepts": student_memory.learned_concepts,
                "confused_points": student_memory.confused_points,
                "questions_asked": student_memory.questions_asked,
                "initial_knowledge_level": student_memory.initial_knowledge_level,
                "current_knowledge_level": student_memory.current_knowledge_level,
                "learning_rate": student_memory.learning_rate,
                "last_updated": datetime.now(),
            }

        return await self._upsert(
            StudentMemoryModel, session_id, update_fn, create_fn
        )
