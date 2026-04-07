"""会话管理 REST API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from orm.message import MessageModel
from orm.teaching_session import TeachingSessionModel

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}/messages", summary="获取会话消息列表")
async def get_session_messages(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """获取指定会话的所有消息，按时间排序.

    Args:
        session_id: 会话 ID
        db: 数据库会话

    Returns:
        消息列表
    """
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.timestamp)
    )
    messages = result.scalars().all()
    return [
        {
            "id": msg.id,
            "session_id": msg.session_id,
            "sender": msg.sender,
            "message_type": msg.message_type,
            "content": msg.content,
            "receiver": msg.receiver or "all",
            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
        }
        for msg in messages
    ]


@router.get("/{session_id}/status", summary="获取会话状态")
async def get_session_status(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取指定会话的状态信息.

    Args:
        session_id: 会话 ID
        db: 数据库会话

    Returns:
        会话状态信息
    """
    result = await db.execute(
        select(TeachingSessionModel).where(TeachingSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {
        "session_id": session.id,
        "topic": session.topic,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }
