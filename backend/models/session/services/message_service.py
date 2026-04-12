"""消息服务 - 统一处理消息广播和持久化."""

from __future__ import annotations

import asyncio
import logging

from agents.memories.memory_persistence import MemoryPersistence
from core.connection_manager import get_connection_manager
from core.database import async_session_maker
from models.session.schemas import Message

logger = logging.getLogger(__name__)


class MessageService:
    """统一消息处理服务.

    职责:
    1. 通过 ConnectionManager 广播消息到 WebSocket
    2. 通过 MemoryPersistence 持久化消息到数据库

    提供两种调用方式:
    - emit_message(): 异步方法，用于观察模式（SessionOrchestrator）
    - emit_message_sync(): 同步方法，用于教师模式（TeacherSessionController）
    """

    def __init__(self, session_id: int):
        self._session_id = session_id

    async def emit_message(self, message: Message) -> None:
        """广播并持久化消息（异步）.

        Args:
            message: Message 对象
        """
        # 1. WebSocket 广播（不依赖 DB）
        cm = get_connection_manager()
        await cm.broadcast(
            self._session_id,
            {
                "type": "message",
                "session_id": self._session_id,
                "sender": message.sender,
                "message_type": message.message_type.value,
                "content": message.content,
                "receiver": message.receiver or "all",
                "timestamp": (message.timestamp.isoformat() if message.timestamp else None),
            },
        )

        # 2. 持久化到数据库（独立 session，避免事务冲突）
        async with async_session_maker() as db:
            persistence = MemoryPersistence(db)
            await persistence.save_message(self._session_id, message)

    def emit_message_sync(self, message: Message) -> None:
        """广播并持久化消息（从同步上下文调用）.

        使用 loop.create_task() 将异步操作调度到事件循环.
        用于 TeacherSessionController 的同步 handle_* 方法.

        Args:
            message: Message 对象
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit_message(message))
        except RuntimeError:
            logger.warning(
                "Message emit skipped: no running event loop (session_id=%d)",
                self._session_id,
            )
