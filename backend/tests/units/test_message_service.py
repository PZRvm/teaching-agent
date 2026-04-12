"""MessageService 单元测试."""

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
) -> Message:
    """辅助方法：创建测试消息."""
    return Message(
        sender=sender,
        message_type=msg_type,
        content=content,
        receiver=receiver,
        timestamp=datetime(2026, 4, 12, 10, 0, 0),
    )


@pytest.mark.asyncio
class TestMessageService:
    """MessageService 单元测试."""

    async def test_emit_message_broadcasts_to_websocket(self):
        """emit_message 通过 ConnectionManager 广播消息."""
        message = _make_message()
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

            mock_persistence = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence

            service = MessageService(session_id=42)
            await service.emit_message(message)

        mock_persistence_cls.assert_called_once_with(mock_db)
        mock_persistence.save_message.assert_awaited_once_with(42, message)

    async def test_emit_message_uses_independent_db_session(self):
        """emit_message 使用独立的数据库会话（不共享请求的 session）."""
        message = _make_message()
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

            service = MessageService(session_id=1)
            await service.emit_message(message)

        mock_session_maker.assert_called_once()

    async def test_emit_message_broadcast_payload_includes_session_id(self):
        """广播 payload 包含 session_id 字段."""
        message = _make_message()
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

            service = MessageService(session_id=99)
            await service.emit_message(message)

        payload = mock_broadcast.call_args[0][1]
        assert payload["session_id"] == 99


class TestMessageServiceSync:
    """MessageService 同步方法测试（不在 async class 中）."""

    def test_emit_message_sync_creates_task(self):
        """emit_message_sync 通过 create_task 调用 emit_message."""
        message = _make_message()

        mock_loop = MagicMock()
        mock_task = MagicMock()
        mock_loop.create_task.return_value = mock_task

        with patch(
            "models.session.services.message_service.asyncio.get_running_loop",
            return_value=mock_loop,
        ):
            service = MessageService(session_id=1)
            service.emit_message_sync(message)

        mock_loop.create_task.assert_called_once()

    def test_emit_message_sync_handles_no_event_loop(self):
        """emit_message_sync 在无事件循环时记录警告，不抛出异常."""
        message = _make_message()

        with patch(
            "models.session.services.message_service.asyncio.get_running_loop",
            side_effect=RuntimeError,
        ):
            service = MessageService(session_id=1)
            service.emit_message_sync(message)
