"""观察模式 API 路由."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.observation.schemas import (
    ObservationConfig,
    ObservationStartResponse,
)
from orm.teaching_session import TeachingSessionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observation", tags=["observation"])


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    创建 teaching_session 记录并返回 session_id。
    注意：实际的 SessionOrchestrator 运行和检查点计划生成
    在 WebSocket 连接建立后异步执行（Phase 10 实现）。

    Args:
        config: 观察模式配置
        db: 数据库会话

    Returns:
        会话 ID 和状态
    """
    # 创建 teaching_session 记录
    session = TeachingSessionModel(
        topic=config.topic,
        teaching_mode=config.teaching_mode,
        students_config=[s.model_dump() for s in config.students],
    )
    db.add(session)
    await db.flush()
    session_id = session.id

    # TODO: Phase 10 - 初始化 StudentAgents、MemoryManager、CheckpointPlan
    # TODO: Phase 10 - 启动 SessionOrchestrator（异步后台任务）
    # TODO: Phase 10 - 返回 WebSocket 连接 URL 供前端连接

    await db.commit()

    logger.info("观察模式会话创建成功 (session_id=%d)", session_id)

    return ObservationStartResponse(
        session_id=session_id,
        status="running",
    )
