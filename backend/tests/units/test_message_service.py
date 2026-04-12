"""MessageService 单元测试."""

from contextlib import contextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.session.schemas import Message, MessageType
from models.session.services.message_service import MessageService


def _make_message(
    sender: str = "teacher",
    msg_type: MessageType = MessageType.LECTURE,
    content: str = "测试消息",
    receiver: str = "all",
    timestamp: datetime | None = datetime(2026, 4, 12, 10, 0, 0),
) -> Message:
    """辅助方法：创建测试消息."""
    return Message(
        sender=sender,
        message_type=msg_type,
        content=content,
        receiver=receiver,
        timestamp=timestamp,
    )


@contextmanager
def _patch_message_service_deps():
    """统一 mock MessageService 的外部依赖."""
    mock_broadcast = AsyncMock()
    mock_cm = MagicMock()
    mock_cm.broadcast = mock_broadcast

    with (
        patch(
            "models.session.services.message_service.get_connection_manager",
            return_value=mock_cm,
        ),
        patch(
            "models.session.services.message_service.async_session_maker"
        ) as mock_session_maker,
        patch(
            "models.session.services.message_service.MemoryPersistence"
        ) as mock_persistence_cls,
    ):
        mock_db = AsyncMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_persistence_cls.return_value = AsyncMock()
        yield mock_cm, mock_session_maker, mock_persistence_cls, mock_broadcast


@pytest.mark.asyncio
class TestMessageService:
    """MessageService 单元测试."""

    async def test_emit_message_broadcasts_to_websocket(self):
        """emit_message 通过 ConnectionManager 广播消息."""
        message = _make_message()

        with _patch_message_service_deps() as (mock_cm, _, _, mock_broadcast):
            service = MessageService(session_id=1)
            await service.emit_message(message)

        mock_broadcast.assert_awaited_once()
        call_args = mock_broadcast.call_args
        assert call_args[0][0] == 1  # session_id
        payload = call_args[0][1]  # message dict
        assert payload["type"] == "message"
        assert payload["session_id"] == 1
        assert payload["sender"] == "teacher"
        assert payload["message_type"] == "lecture"
        assert payload["content"] == "测试消息"
        assert payload["receiver"] == "all"
        assert payload["timestamp"] == "2026-04-12T10:00:00"

    async def test_emit_message_persists_to_database(self):
        """emit_message 持久化消息到数据库."""
        message = _make_message()

        with _patch_message_service_deps() as (_, _, mock_persistence_cls, _):
            mock_persistence = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence

            service = MessageService(session_id=42)
            await service.emit_message(message)

        mock_persistence_cls.assert_called_once()
        mock_persistence.save_message.assert_awaited_once_with(42, message)

    async def test_emit_message_uses_independent_db_session(self):
        """emit_message 使用独立的数据库会话（不共享请求的 session）."""
        message = _make_message()

        with _patch_message_service_deps() as (_, mock_session_maker, _, _):
            service = MessageService(session_id=1)
            await service.emit_message(message)

        mock_session_maker.assert_called_once()

    async def test_emit_message_broadcast_payload_includes_session_id(self):
        """广播 payload 包含 session_id 字段."""
        message = _make_message()

        with _patch_message_service_deps() as (_, _, _, mock_broadcast):
            service = MessageService(session_id=99)
            await service.emit_message(message)

        payload = mock_broadcast.call_args[0][1]
        assert payload["session_id"] == 99

    async def test_emit_message_broadcast_with_empty_receiver_defaults_to_all(self):
        """emit_message 广播时 receiver 为空字符串默认为 'all'."""
        message = _make_message(receiver="")

        with _patch_message_service_deps() as (_, _, _, mock_broadcast):
            service = MessageService(session_id=1)
            await service.emit_message(message)

        payload = mock_broadcast.call_args[0][1]
        assert payload["receiver"] == "all"

    async def test_emit_message_broadcast_with_null_timestamp(self):
        """emit_message 广播时 timestamp 为 None 时 payload 中 timestamp 也为 None."""
        message = _make_message(timestamp=None)

        with _patch_message_service_deps() as (_, _, _, mock_broadcast):
            service = MessageService(session_id=1)
            await service.emit_message(message)

        payload = mock_broadcast.call_args[0][1]
        assert payload["timestamp"] is None

    async def test_emit_message_persists_even_if_broadcast_fails(self):
        """emit_message 在广播失败时仍然执行持久化."""
        message = _make_message()

        with _patch_message_service_deps() as (mock_cm, _, mock_persistence_cls, _):
            mock_cm.broadcast = AsyncMock(side_effect=RuntimeError("WS error"))
            mock_persistence = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence

            service = MessageService(session_id=1)
            await service.emit_message(message)

        mock_persistence.save_message.assert_awaited_once_with(1, message)

    async def test_emit_message_broadcasts_even_if_persistence_fails(self):
        """emit_message 在持久化失败时仍然执行广播."""
        message = _make_message()

        with _patch_message_service_deps() as (_, _, mock_persistence_cls, mock_broadcast):
            mock_persistence = AsyncMock()
            mock_persistence.save_message.side_effect = Exception("DB write failed")
            mock_persistence_cls.return_value = mock_persistence

            service = MessageService(session_id=1)
            await service.emit_message(message)

        mock_broadcast.assert_awaited_once()

    async def test_emit_message_sync_enqueues_message(self):
        """emit_message_sync 将消息放入队列，由消费者按顺序处理."""
        message = _make_message()

        mock_loop = MagicMock()

        with patch(
            "models.session.services.message_service.asyncio.get_running_loop",
            return_value=mock_loop,
        ):
            service = MessageService(session_id=1)
            # 直接 mock _ensure_consumer 避免创建真实的 asyncio task
            service._ensure_consumer = MagicMock()
            service.emit_message_sync(message)

        # 消息应该被放入队列
        assert service._queue.qsize() == 1
        queued = service._queue.get_nowait()
        assert queued.sender == "teacher"
        assert queued.content == "测试消息"

    async def test_emit_message_sync_handles_no_event_loop(self):
        """emit_message_sync 在无事件循环时记录警告，不抛出异常."""
        message = _make_message()

        with patch(
            "models.session.services.message_service.asyncio.get_running_loop",
            side_effect=RuntimeError,
        ):
            service = MessageService(session_id=1)
            service.emit_message_sync(message)

        assert service._queue.qsize() == 0
