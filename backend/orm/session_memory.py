"""会话记忆 ORM 模型"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import JSON, DateTime, ForeignKey, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SessionMemoryModel(Base, AsyncAttrs):
    """会话记忆表"""

    __tablename__ = "session_memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("teaching_sessions.id"))
    message_history: Mapped[list] = mapped_column(JSON)
    teaching_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai"))
    )
