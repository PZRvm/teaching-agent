"""观察模式 API 路由."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import MemoryManager
from agents.student_agent import StudentAgent
from core.database import get_db
from core.llm_client import LLMClient
from models.checkpoint.persistence_service import CheckpointPlanPersistence
from models.checkpoint.service import CheckpointPlanService
from models.observation.schemas import (
    ObservationConfig,
    ObservationStartResponse,
)
from models.session.orchestrator import SessionOrchestrator
from models.session.router_websocket import get_session_registry
from orm.teaching_session import TeachingSessionModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observation", tags=["observation"])


def _create_llm_client() -> LLMClient:
    """创建 LLM 客户端（从配置加载）."""
    import os
    from pathlib import Path

    import yaml

    config_path = Path(__file__).parents[2] / "configs" / "llm.yml"
    with open(config_path) as f:
        llm_config = yaml.safe_load(f)

    return LLMClient(
        base_url=llm_config["llm"]["base_url"],
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        model=llm_config["llm"]["model"],
        temperature=llm_config["llm"]["temperature"],
    )


def _create_teacher_agent(llm: LLMClient, memory_manager: MemoryManager, teaching_mode: str):
    """创建教师 Agent."""
    from agents.teacher_agent import TeacherAgent

    return TeacherAgent(
        session_memory=memory_manager.session_memory,
        llm=llm,
        memory_manager=memory_manager,
        teaching_mode=teaching_mode,
    )


def _create_student_agents(
    students_config: list[dict], llm: LLMClient, memory_manager: MemoryManager
) -> list[StudentAgent]:
    """从配置创建学生 Agent 列表."""
    from schemas.student import StudentProfile

    agents = []
    for s_config in students_config:
        profile = StudentProfile(**s_config)
        agent = StudentAgent(
            session_memory=memory_manager.session_memory,
            llm=llm,
            profile=profile,
        )
        agents.append(agent)
    return agents


def _create_memory_manager(session_id: int, topic: str) -> MemoryManager:
    """创建 MemoryManager."""
    from agents.memories import SessionMemory, TeacherAgentMemory

    session_memory = SessionMemory(session_id=session_id, topic=topic)
    teacher_memory = TeacherAgentMemory()
    return MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)


async def _generate_checkpoint_plan(
    topic: str, teaching_mode: str, checkpoint_count: int, llm: LLMClient
):
    """生成检查点计划."""
    service = CheckpointPlanService(llm)
    return await service.generate_plan(topic, teaching_mode, checkpoint_count)


async def _run_orchestrator_background(
    session_id: int,
    topic: str,
    teaching_mode: str,
    checkpoint_count: int,
    students_config: list[dict],
) -> None:
    """后台初始化并运行 orchestrator.

    此函数负责：
    1. 推送 initializing 状态事件
    2. 初始化 LLM、agents、memory manager
    3. 生成检查点计划
    4. 持久化检查点计划
    5. 创建并注册 orchestrator
    6. 推送 running 状态事件
    7. 运行教学流程
    8. 清理资源（unregister）

    Args:
        session_id: 会话 ID
        topic: 教学主题
        teaching_mode: 教学模式
        checkpoint_count: 检查点数量
        students_config: 学生配置列表
    """
    from core.connection_manager import get_connection_manager
    from core.database import async_session_maker

    cm = get_connection_manager()
    registry = get_session_registry()

    # 创建新的数据库 session（后台任务独立于请求的 session）
    async with async_session_maker() as db:
        try:
            # 1. 推送初始化中状态
            await cm.broadcast(
                session_id,
                {
                    "type": "session_state",
                    "session_id": session_id,
                    "teaching_mode": teaching_mode,
                    "status": "initializing",
                },
            )

            # 2. 初始化 LLM、agents、memory manager
            llm = _create_llm_client()
            memory_manager = _create_memory_manager(session_id, topic)
            teacher_agent = _create_teacher_agent(llm, memory_manager, teaching_mode)
            student_agents = _create_student_agents(students_config, llm, memory_manager)

            # 3. 生成检查点计划（慢 LLM 调用）
            checkpoint_plan = await _generate_checkpoint_plan(
                topic, teaching_mode, checkpoint_count, llm
            )

            # 4. 持久化
            persistence = CheckpointPlanPersistence(db)
            await persistence.save_plan(session_id, checkpoint_plan)

            # 5. 创建并注册 orchestrator
            orchestrator = SessionOrchestrator(
                teacher_agent=teacher_agent,
                student_agents=student_agents,
                checkpoint_plan=checkpoint_plan,
                memory_manager=memory_manager,
            )
            registry.register_orchestrator(session_id, orchestrator)

            # 6. 推送就绪状态
            await cm.broadcast(
                session_id,
                {
                    "type": "session_state",
                    "session_id": session_id,
                    "teaching_mode": teaching_mode,
                    "status": "running",
                },
            )

            # 7. 运行教学流程
            await orchestrator.run_autonomous_session()

        except Exception as e:
            logger.error(
                "观察模式后台任务失败 (session_id=%d): %s",
                session_id,
                e,
                exc_info=True,
            )
            # 推送错误状态
            import contextlib

            with contextlib.suppress(Exception):
                await cm.broadcast(
                    session_id,
                    {
                        "type": "session_state",
                        "session_id": session_id,
                        "status": "error",
                        "message": str(e),
                    },
                )

        finally:
            # 8. 清理资源
            registry.unregister(session_id)
            logger.info("观察模式会话已清理 (session_id=%d)", session_id)


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    创建 teaching_session 记录，注册 session 到 SessionRegistry，
    后台异步完成初始化和教学流程。

    Args:
        config: 观察模式配置
        db: 数据库会话
        background_tasks: FastAPI 后台任务

    Returns:
        会话 ID 和状态（immediate 返回，status="initializing"）
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
        _run_orchestrator_background,
        session_id=session_id,
        topic=config.topic,
        teaching_mode=config.teaching_mode,
        checkpoint_count=config.checkpoint_count,
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
    """获取观察会话的当前状态.

    用于前端验证 session 是否仍然有效。

    Args:
        session_id: 会话 ID

    Returns:
        会话状态信息
    """
    from models.session.router_websocket import get_session_registry

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
