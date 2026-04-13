"""学生记忆 ORM 模型."""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from schemas.student import StudentAttitude, StudentLevel


class StudentMemoryModel(Base):
    """学生记忆 ORM 模型."""

    __tablename__ = "student_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(sa.ForeignKey("teaching_sessions.id"))
    student_name: Mapped[str] = mapped_column(sa.String(50))
    level: Mapped[StudentLevel] = mapped_column(sa.Enum(StudentLevel), default=StudentLevel.AVERAGE)
    attitude: Mapped[StudentAttitude] = mapped_column(
        sa.Enum(StudentAttitude), default=StudentAttitude.NEUTRAL
    )
    learning_ability: Mapped[int] = mapped_column(sa.Integer, default=5)

    learned_concepts: Mapped[list[str]] = mapped_column(sa.JSON, default=list)
    confused_points: Mapped[list[str]] = mapped_column(sa.JSON, default=list)
    questions_asked: Mapped[list[str]] = mapped_column(sa.JSON, default=list)

    initial_knowledge_level: Mapped[float] = mapped_column(sa.Float, default=0.0)
    current_knowledge_level: Mapped[float] = mapped_column(sa.Float, default=0.0)
    learning_rate: Mapped[float] = mapped_column(sa.Float, default=0.05)

    last_updated: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=datetime.now, onupdate=datetime.now
    )

    __table_args__ = (
        sa.Index("ix_student_memories_session_id", "session_id"),
        sa.Index("ix_student_memories_session_student", "session_id", "student_name"),
    )
