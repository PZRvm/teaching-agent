"""观察模式 API 路由."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.session_registry import get_session_registry
from models.checkpoint.schemas import CheckpointState
from models.checkpoint.services.persistence_service import CheckpointPlanPersistence
from models.observation.schemas import (
    CheckpointProgressCounts,
    CheckpointProgressInfo,
    CheckpointProgressResponse,
    ObservationConfig,
    ObservationStartResponse,
)
from models.observation.service import _run_background_task
from orm.teaching_session import TeachingSessionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observation", tags=["observation"])


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    创建 teaching_session 记录，注册 session 到 SessionRegistry，
    后台异步完成初始化和教学流程。
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
    await db.commit()

    # 注册 session（仅 mode，无 orchestrator）
    registry = get_session_registry()
    registry.register(session_id=session_id, mode="observation")

    # 后台执行所有初始化 + 教学
    background_tasks.add_task(
        _run_background_task,
        session_id=session_id,
        topic=config.topic,
        teaching_mode=config.teaching_mode,
        students_config=[s.model_dump() for s in config.students],
    )

    logger.info(
        "观察模式会话启动成功 (session_id=%d, students=%d)",
        session_id,
        len(config.students),
    )

    return ObservationStartResponse(
        session_id=session_id,
        status="initializing",
    )


@router.get("/{session_id}/status", summary="获取观察会话状态")
async def get_observation_status(session_id: int) -> dict[str, Any]:
    """获取观察会话的当前状态."""
    registry = get_session_registry()
    session_info = registry.get_session_info(session_id)

    if session_info is None:
        return {"exists": False, "message": "Session 不存在或已结束"}

    orchestrator = registry.get_orchestrator(session_id) if session_info["mode"] == "observation" else None

    return {
        "exists": True,
        "mode": session_info["mode"],
        "ready": orchestrator is not None,
    }


@router.get(
    "/{session_id}/checkpoint-progress",
    summary="获取检查点进度",
    response_model=CheckpointProgressResponse,
)
async def get_checkpoint_progress(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckpointProgressResponse:
    """获取当前检查点进度（索引、当前检查点信息、进度计数）.

    数据源优先级：
    1. orchestrator 在内存中运行时使用其实时数据
    2. 否则回退到数据库中持久化的检查点计划
    """
    registry = get_session_registry()
    orchestrator = registry.get_orchestrator(session_id)

    if orchestrator is not None:
        plan = orchestrator.checkpoint_plan
    else:
        service = CheckpointPlanPersistence(db)
        plan = await service.load_plan(session_id=session_id)

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint plan for session {session_id} not found",
        )

    idx = plan.current_index
    current_cp = plan.checkpoints[idx]

    return CheckpointProgressResponse(
        index=idx,
        checkpoint=CheckpointProgressInfo(
            title=current_cp.title,
            state=current_cp.state.value,
            key_point=current_cp.key_point,
        ),
        progress=CheckpointProgressCounts(
            current=idx + 1,
            total=len(plan.checkpoints),
            completed=sum(
                1 for cp in plan.checkpoints[:idx]
                if cp.state == CheckpointState.COMPLETE
            ),
        ),
        checkpoints=[
            CheckpointProgressInfo(
                title=cp.title,
                state=cp.state.value,
                key_point=cp.key_point,
            )
            for cp in plan.checkpoints
        ],
    )
