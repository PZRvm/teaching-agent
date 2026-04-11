"""Checkpoint API 路由."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from models.checkpoint.services.persistence_service import CheckpointPlanPersistence

router = APIRouter(prefix="/checkpoint-plans", tags=["checkpoint-plans"])


# Request/Response Schemas
class CheckpointPlanCreate(BaseModel):
    """创建检查点计划请求."""

    topic: str
    teaching_mode: str
    checkpoints: list[Checkpoint]


class UpdateCheckpointState(BaseModel):
    """更新检查点状态请求."""

    new_state: str = Field(description="新状态: pending, teaching, questions, complete")


class CheckpointPlanResponse(BaseModel):
    """检查点计划响应."""

    plan_id: int


@router.post("/", summary="创建检查点计划", response_model=CheckpointPlanResponse)
async def create_checkpoint_plan(
    session_id: int,
    plan_data: CheckpointPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckpointPlanResponse:
    """创建检查点计划.

    Args:
        session_id: 教学会话 ID
        plan_data: 检查点计划数据

    Returns:
        创建的记录 ID
    """
    plan = CheckpointPlan(
        topic=plan_data.topic,
        teaching_mode=plan_data.teaching_mode,
        checkpoints=plan_data.checkpoints,
    )

    service = CheckpointPlanPersistence(db)
    plan_id = await service.save_plan(session_id=session_id, plan=plan)

    return CheckpointPlanResponse(plan_id=plan_id)


@router.get("/{session_id}", summary="获取检查点计划", response_model=CheckpointPlan)
async def get_checkpoint_plan(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckpointPlan:
    """获取指定会话的检查点计划.

    Args:
        session_id: 教学会话 ID

    Returns:
        检查点计划

    Raises:
        HTTPException: 计划不存在时返回 404
    """
    service = CheckpointPlanPersistence(db)
    plan = await service.load_plan(session_id=session_id)

    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint plan for session {session_id} not found",
        )

    return plan


@router.put("/{session_id}", summary="编辑检查点计划")
async def edit_checkpoint_plan(
    session_id: int,
    plan_data: CheckpointPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, bool]:
    """编辑检查点计划.

    只能在所有检查点都是 PENDING 状态时编辑。

    Args:
        session_id: 教学会话 ID
        plan_data: 新的检查点计划数据

    Returns:
        成功消息

    Raises:
        HTTPException: 计划不存在或教学已开始时返回错误
    """
    plan = CheckpointPlan(
        topic=plan_data.topic,
        teaching_mode=plan_data.teaching_mode,
        checkpoints=plan_data.checkpoints,
    )

    service = CheckpointPlanPersistence(db)
    try:
        await service.update_plan(session_id=session_id, plan=plan)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from None
        else:
            # Teaching has already started
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from None

    return {"success": True}


@router.put(
    "/{session_id}/checkpoints/{checkpoint_index}/state",
    summary="更新检查点状态",
)
async def update_checkpoint_state(
    session_id: int,
    checkpoint_index: int,
    request: UpdateCheckpointState,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """更新指定检查点的状态.

    Args:
        session_id: 教学会话 ID
        checkpoint_index: 检查点索引
        request: 包含 new_state 的请求体

    Returns:
        成功消息

    Raises:
        HTTPException: 状态值无效或计划不存在时返回错误
    """
    # 验证状态值
    try:
        new_state = CheckpointState(request.new_state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state: {request.new_state}. Must be one of: pending, teaching, questions, complete",
        ) from None

    service = CheckpointPlanPersistence(db)
    try:
        await service.update_checkpoint_state(
            session_id=session_id,
            checkpoint_index=checkpoint_index,
            new_state=new_state,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    return {"message": "Checkpoint state updated successfully"}


@router.put("/{session_id}/advance", summary="推进到下一个检查点", response_model=CheckpointPlan)
async def advance_checkpoint(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CheckpointPlan:
    """推进到下一个检查点.

    将 current_index 加 1，并将新当前检查点状态设为 TEACHING。

    Args:
        session_id: 教学会话 ID

    Returns:
        更新后的检查点计划

    Raises:
        HTTPException: 计划不存在或无法推进时返回错误
    """
    service = CheckpointPlanPersistence(db)

    try:
        await service.advance_checkpoint(session_id=session_id)
    except ValueError as e:
        # Checkpoint plan not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None
    except IndexError as e:
        # Already at last checkpoint
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    plan = await service.load_plan(session_id=session_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checkpoint plan for session {session_id} not found",
        )

    return plan


@router.delete("/{session_id}", summary="删除检查点计划")
async def delete_checkpoint_plan(
    session_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """删除指定会话的检查点计划.

    Args:
        session_id: 教学会话 ID

    Returns:
        成功消息
    """
    service = CheckpointPlanPersistence(db)
    await service.delete_plan(session_id=session_id)

    return {"message": "Checkpoint plan deleted successfully"}
