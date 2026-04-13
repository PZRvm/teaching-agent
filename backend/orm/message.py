"""消息 ORM 模型"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class MessageModel(Base, AsyncAttrs):
    """消息表"""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("teaching_sessions.id"))
    sender: Mapped[str] = mapped_column(String(50))
    message_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    receiver: Mapped[str] = mapped_column(String(50), default="all")
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Asia/Shanghai"))
    )
