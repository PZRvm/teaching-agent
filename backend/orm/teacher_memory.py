"""教师记忆 ORM 模型"""

from sqlalchemy import JSON, Float, ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TeacherMemoryModel(Base, AsyncAttrs):
    """教师记忆表"""

    __tablename__ = "teacher_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("teaching_sessions.id"))
    covered_topics: Mapped[list] = mapped_column(JSON)
    student_questions: Mapped[dict] = mapped_column(JSON)
    student_participation: Mapped[dict] = mapped_column(JSON)
    teaching_progress: Mapped[float] = mapped_column(Float, default=0.0)
    student_misconceptions: Mapped[dict] = mapped_column(JSON)
