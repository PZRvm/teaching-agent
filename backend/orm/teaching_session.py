"""教学会话 ORM 模型"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TeachingSessionModel(Base, AsyncAttrs):
    """教学会话表"""

    __tablename__ = "teaching_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teaching_mode: Mapped[str] = mapped_column(String(20))
    topic: Mapped[str] = mapped_column(String(200))
    students_config: Mapped[dict] = mapped_column(JSON)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")
    start_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Shanghai"))
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
