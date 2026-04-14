"""观察模式业务逻辑服务."""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from sqlalchemy import select

from agents.memories.memory_manager import MemoryManager
from agents.student_agent import StudentAgent
from core.connection_manager import get_connection_manager
from core.database import async_session_maker
from core.llm_client import LLMClient
from core.session_registry import get_session_registry
from models.checkpoint.services.persistence_service import CheckpointPlanPersistence
from models.checkpoint.services.plan_service import CheckpointPlanService
from models.session.services.observation_service import SessionOrchestrator
from orm.teaching_session import TeachingSessionModel

logger = logging.getLogger(__name__)


def _create_llm_client(model_key: str = "model") -> LLMClient:
    """创建 LLM 客户端（从配置加载）.

    Args:
        model_key: 配置中的模型字段名，"model" 用于学生，"teacher_model" 用于教师
    """
    import os

    config_path = Path(__file__).parents[2] / "configs" / "llm.yml"
    with open(config_path) as f:
        llm_config = yaml.safe_load(f)

    return LLMClient(
        base_url=llm_config["llm"]["base_url"],
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        model=llm_config["llm"][model_key],
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
    topic: str, teaching_mode: str, llm: LLMClient
):
    """生成检查点计划."""
    service = CheckpointPlanService(llm)
    return await service.generate_plan(topic, teaching_mode)


async def _run_background_task(
    session_id: int,
    topic: str,
    teaching_mode: str,
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
    """
    cm = get_connection_manager()
    registry = get_session_registry()

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
        # 教师使用 72B 模型（更大上下文窗口，方便课后总结）
        teacher_llm = _create_llm_client(model_key="teacher_model")
        # 学生使用 7B 模型
        student_llm = _create_llm_client(model_key="model")
        memory_manager = _create_memory_manager(session_id, topic)
        teacher_agent = _create_teacher_agent(teacher_llm, memory_manager, teaching_mode)
        student_agents = _create_student_agents(students_config, student_llm, memory_manager)

        # 3. 生成检查点计划（慢 LLM 调用，使用教师模型保证质量）
        checkpoint_plan = await _generate_checkpoint_plan(
            topic, teaching_mode, teacher_llm
        )

        # 4. 持久化检查点计划（用完即释放连接，不长期占用）
        async with async_session_maker() as db:
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
        with contextlib.suppress(Exception):
            await cm.broadcast(
                session_id,
                {
                    "type": "session_state",
                    "session_id": session_id,
                    "status": "error",
                    "message": "Session initialization failed",
                },
            )
        # 标记会话为中断
        with contextlib.suppress(Exception):
            async with async_session_maker() as db:
                await finalize_session(
                    db=db,
                    session_id=session_id,
                    status="interrupted",
                )
                await db.commit()

    finally:
        # 8. 清理资源
        orchestrator = registry.get_orchestrator(session_id)
        if orchestrator is not None:
            await orchestrator.stop()
        registry.unregister(session_id)

        # 9. 更新会话生命周期状态
        with contextlib.suppress(Exception):
            async with async_session_maker() as db:
                await finalize_session(
                    db=db,
                    session_id=session_id,
                    status="completed",
                )
                await db.commit()

        logger.info("观察模式会话已清理 (session_id=%d)", session_id)


async def finalize_session(
    *,
    db,
    session_id: int,
    status: str,
) -> None:
    """更新会话的结束状态.

    Args:
        db: 数据库会话
        session_id: 会话 ID
        status: 结束状态（"completed" 或 "interrupted"）
    """
    result = await db.execute(
        select(TeachingSessionModel).where(TeachingSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"会话不存在 (session_id={session_id})")

    session.status = status
    session.end_time = datetime.now(ZoneInfo("Asia/Shanghai"))
    if session.start_time and session.end_time:
        try:
            session.duration_seconds = int(
                (session.end_time - session.start_time).total_seconds()
            )
        except TypeError:
            # start_time 可能是 naive datetime，添加时区后重试
            if session.start_time.tzinfo is None:
                start_aware = session.start_time.replace(
                    tzinfo=ZoneInfo("Asia/Shanghai")
                )
                session.duration_seconds = int(
                    (session.end_time - start_aware).total_seconds()
                )
    await db.flush()
