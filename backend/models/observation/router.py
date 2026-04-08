"""观察模式 API 路由."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents.memories.memory_manager import MemoryManager
from agents.student_agent import StudentAgent
from models.checkpoint.persistence_service import CheckpointPlanPersistence
from models.checkpoint.service import CheckpointPlanService
from core.database import get_db
from core.llm_client import LLMClient
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


def _create_teacher_agent(
    llm: LLMClient, memory_manager: MemoryManager, teaching_mode: str
):
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


async def _run_orchestrator_background(session_id: int, orchestrator: SessionOrchestrator) -> None:
    """后台运行 orchestrator 自动教学流程."""
    try:
        await orchestrator.run_autonomous_session()
    except Exception as e:
        logger.error("Orchestrator 运行失败 (session_id=%d): %s", session_id, e, exc_info=True)
    finally:
        get_session_registry().unregister(session_id)
        logger.info("Orchestrator 已清理 (session_id=%d)", session_id)


@router.post("/start", summary="启动观察模式会话", response_model=ObservationStartResponse)
async def start_observation(
    config: ObservationConfig,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> ObservationStartResponse:
    """启动观察模式自动教学会话.

    创建 teaching_session 记录，初始化 SessionOrchestrator，
    注册到 SessionRegistry，后台异步运行教学流程。

    Args:
        config: 观察模式配置
        db: 数据库会话
        background_tasks: FastAPI 后台任务

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
    await db.commit()

    # 初始化 LLM 和 agents
    llm = _create_llm_client()
    memory_manager = _create_memory_manager(session_id, config.topic)
    teacher_agent = _create_teacher_agent(llm, memory_manager, config.teaching_mode)
    student_agents = _create_student_agents(
        [s.model_dump() for s in config.students], llm, memory_manager
    )

    # 生成检查点计划
    checkpoint_plan = await _generate_checkpoint_plan(
        config.topic, config.teaching_mode, config.checkpoint_count, llm
    )

    # 持久化检查点计划
    persistence = CheckpointPlanPersistence(db)
    await persistence.save_plan(session_id, checkpoint_plan)

    # 创建 orchestrator
    orchestrator = SessionOrchestrator(
        teacher_agent=teacher_agent,
        student_agents=student_agents,
        checkpoint_plan=checkpoint_plan,
        memory_manager=memory_manager,
    )

    # 注册到 SessionRegistry（WebSocket 端点可通过 session_id 找到 orchestrator）
    registry = get_session_registry()
    registry.register(session_id=session_id, mode="observation", orchestrator=orchestrator)

    # 后台运行教学流程
    background_tasks.add_task(_run_orchestrator_background, session_id, orchestrator)

    logger.info(
        "观察模式会话启动成功 (session_id=%d, students=%d, checkpoints=%d)",
        session_id,
        len(student_agents),
        len(checkpoint_plan.checkpoints),
    )

    return ObservationStartResponse(
        session_id=session_id,
        status="running",
    )
