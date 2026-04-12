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
    3. 通过 asyncio.Queue 保证消息顺序（emit_message_sync 路径）

    提供两种调用方式:
    - emit_message(): 异步方法，用于观察模式（SessionOrchestrator）
    - emit_message_sync(): 同步方法，用于教师模式（TeacherSessionController）
      通过队列序列化，保证消息按调用顺序处理。
    """

    def __init__(self, session_id: int):
        self._session_id = session_id
        self._queue: asyncio.Queue[Message | None] = asyncio.Queue()
        self._consumer_task: asyncio.Task | None = None

    def _ensure_consumer(self) -> None:
        """确保消费者任务在运行."""
        if self._consumer_task is None or self._consumer_task.done():
            self._consumer_task = asyncio.ensure_future(self._consume_queue())

    async def _consume_queue(self) -> None:
        """后台消费者：按顺序处理队列中的消息."""
        while True:
            message = await self._queue.get()
            if message is None:
                break  # 停止信号
            try:
                await self.emit_message(message)
            except Exception:
                logger.exception(
                    "Queue consumer error (session_id=%d)",
                    self._session_id,
                )
            finally:
                self._queue.task_done()

    async def stop(self) -> None:
        """停止消费者任务，等待队列清空."""
        await self._queue.put(None)  # 发送停止信号
        if self._consumer_task is not None:
            await self._consumer_task

    async def emit_message(self, message: Message) -> None:
        """广播并持久化消息（异步）.

        Args:
            message: Message 对象
        """
        # 1. WebSocket 广播（不依赖 DB）
        try:
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
        except Exception:
            logger.exception(
                "WebSocket broadcast failed (session_id=%d, sender=%s)",
                self._session_id,
                message.sender,
            )

        # 2. 持久化到数据库（独立 session，避免事务冲突）
        try:
            async with async_session_maker() as db:
                persistence = MemoryPersistence(db)
                await persistence.save_message(self._session_id, message)
        except Exception:
            logger.exception(
                "Message persistence failed (session_id=%d, sender=%s)",
                self._session_id,
                message.sender,
            )

    def emit_message_sync(self, message: Message) -> None:
        """广播并持久化消息（从同步上下文调用）.

        将消息放入队列，由后台消费者按顺序处理。
        用于 TeacherSessionController 的同步 handle_* 方法。

        Args:
            message: Message 对象
        """
        try:
            asyncio.get_running_loop()  # 确认事件循环在运行
            # 确保消费者在运行（同步方法，直接调用）
            self._ensure_consumer()
            # 将消息放入队列
            self._queue.put_nowait(message)
        except RuntimeError:
            logger.warning(
                "Message emit skipped: no running event loop (session_id=%d)",
                self._session_id,
            )
