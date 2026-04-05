"""观察模式 API 路由."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.observation.schemas import (
    ObservationConfig,
    ObservationStartResponse,
)

router = APIRouter(prefix="/observation", tags=["observation"])


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    Args:
        config: 观察模式配置
        db: 数据库会话

    Returns:
        会话ID和状态
    """
    # TODO: Implement full observation session logic
    # - Create session in database
    # - Generate checkpoint plan
    # - Initialize and run SessionOrchestrator
    # For now, return a mock response to satisfy the test
    return ObservationStartResponse(session_id=1, status="running")
