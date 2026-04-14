"""会话管理 REST API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from orm.checkpoint_plan import CheckpointPlanModel
from orm.message import MessageModel
from orm.teaching_session import TeachingSessionModel

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _build_checkpoint_progress(plan_data: dict | None) -> dict | None:
    """从 checkpoint plan JSON 中提取进度信息."""
    if plan_data is None:
        return None
    checkpoints = plan_data.get("checkpoints", [])
    return {
        "total": len(checkpoints),
        "completed": sum(
            1 for cp in checkpoints if cp.get("state") == "complete"
        ),
        "current_index": plan_data.get("current_index", 0),
    }


def _session_to_dict(session: TeachingSessionModel, checkpoint_progress: dict | None) -> dict:
    """将 TeachingSessionModel 序列化为 API 响应字典."""
    return {
        "id": session.id,
        "topic": session.topic,
        "teaching_mode": session.teaching_mode,
        "status": session.status,
        "start_time": (
            session.start_time.isoformat() if session.start_time else None
        ),
        "end_time": (
            session.end_time.isoformat() if session.end_time else None
        ),
        "duration_seconds": session.duration_seconds,
        "student_count": len(session.students_config) if session.students_config else 0,
        "checkpoint_progress": checkpoint_progress,
    }


@router.get("/", summary="获取会话列表")
async def get_session_list(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """获取所有会话列表，按开始时间倒序.

    Args:
        db: 数据库会话
        limit: 返回数量上限，默认 50
        offset: 偏移量，默认 0

    Returns:
        会话列表，包含基本信息和检查点进度
    """
    stmt = (
        select(TeachingSessionModel, CheckpointPlanModel.plan_data)
        .outerjoin(
            CheckpointPlanModel,
            TeachingSessionModel.id == CheckpointPlanModel.session_id,
        )
        .order_by(TeachingSessionModel.start_time.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for session, plan_data in rows:
        items.append(_session_to_dict(session, _build_checkpoint_progress(plan_data)))

    return items


@router.get("/{session_id}", summary="获取单个会话详情")
async def get_session_detail(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取指定会话的详情，包含检查点进度.

    Args:
        session_id: 会话 ID
        db: 数据库会话

    Returns:
        会话详情

    Raises:
        HTTPException: 会话不存在时返回 404
    """
    result = await db.execute(
        select(TeachingSessionModel).where(TeachingSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    plan_result = await db.execute(
        select(CheckpointPlanModel.plan_data).where(
            CheckpointPlanModel.session_id == session_id
        )
    )
    plan_data = plan_result.scalar_one_or_none()
    checkpoint_progress = _build_checkpoint_progress(plan_data)

    return _session_to_dict(session, checkpoint_progress)


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
