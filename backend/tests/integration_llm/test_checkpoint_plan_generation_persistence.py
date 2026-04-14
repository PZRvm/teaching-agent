"""LLM 检查点计划生成 + 持久化集成测试（真实 LLM）.

验证链路: 真实 LLM → CheckpointPlanService.generate_plan() → CheckpointPlanPersistence → 数据库

运行方式:
    pytest tests/integration_llm/test_checkpoint_plan_generation_persistence.py -v -s -m integration
"""

import asyncio

import pytest


@pytest.mark.integration
def test_llm_checkpoint_plan_generated_and_persisted():
    """测试: 真实 LLM 生成检查点计划 → 持久化到数据库 → 加载验证."""
    from dotenv import load_dotenv

    load_dotenv()

    async def _test():
        from core.llm_client import LLMClient
        from models.checkpoint.services.persistence_service import CheckpointPlanPersistence
        from models.checkpoint.services.plan_service import CheckpointPlanService

        llm = LLMClient.from_config()

        # 生成检查点计划
        print("\n[1/3] 调用 LLM 生成检查点计划...")
        service = CheckpointPlanService(llm=llm)
        plan = await service.generate_plan(
            topic="Python 变量与数据类型",
            teaching_mode="didactic",
        )

        print("\n[LLM 输出] 生成的检查点计划:")
        print(f"  主题: {plan.topic}")
        print(f"  教学模式: {plan.teaching_mode}")
        print(f"  检查点数量: {len(plan.checkpoints)}")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"\n  检查点 {i}:")
            print(f"    标题: {cp.title}")
            print(f"    核心知识点: {cp.key_point}")
            print(f"    检查问题: {cp.checkpoint_question}")

        # 持久化到数据库
        print("\n[2/3] 持久化到数据库...")
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from core.database import Base
        from orm.checkpoint_plan import CheckpointPlanModel  # noqa: F401

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session_maker() as db:
            persistence = CheckpointPlanPersistence(db_session=db)
            record_id = await persistence.save_plan(session_id=100, plan=plan)
            print(f"  保存成功, record_id={record_id}")

        # 从数据库加载并验证
        print("\n[3/3] 从数据库加载并验证...")
        async with async_session_maker() as db:
            persistence = CheckpointPlanPersistence(db_session=db)
            loaded_plan = await persistence.load_plan(session_id=100)

        assert loaded_plan is not None
        assert loaded_plan.topic == plan.topic
        assert loaded_plan.teaching_mode == plan.teaching_mode
        assert len(loaded_plan.checkpoints) == len(plan.checkpoints)
        print("  加载验证通过!")
        print(f"  主题: {loaded_plan.topic}")
        print(f"  教学模式: {loaded_plan.teaching_mode}")
        print(f"  检查点数量: {len(loaded_plan.checkpoints)}")

        await engine.dispose()

    asyncio.run(_test())


@pytest.mark.integration
def test_llm_checkpoint_plan_heuristic_mode():
    """测试: 真实 LLM 生成启发式检查点计划."""
    from dotenv import load_dotenv

    load_dotenv()

    async def _test():
        from core.llm_client import LLMClient
        from models.checkpoint.services.plan_service import CheckpointPlanService

        llm = LLMClient.from_config()

        print("\n[1/2] 调用 LLM 生成启发式检查点计划...")
        service = CheckpointPlanService(llm=llm)
        plan = await service.generate_plan(
            topic="Python 函数基础",
            teaching_mode="heuristic",
        )

        print("\n[LLM 输出] 生成的检查点计划:")
        print(f"  主题: {plan.topic}")
        print(f"  教学模式: {plan.teaching_mode}")
        print(f"  检查点数量: {len(plan.checkpoints)}")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"\n  检查点 {i}:")
            print(f"    标题: {cp.title}")
            print(f"    核心知识点: {cp.key_point}")
            print(f"    检查问题: {cp.checkpoint_question}")

        # 验证（topic 用模糊匹配，LLM 输出可能微调措辞）
        assert "Python" in plan.topic and "函数" in plan.topic
        assert plan.teaching_mode == "heuristic"
        # LLM 输出非确定性，确保至少生成 1 个检查点
        assert len(plan.checkpoints) >= 1

        print("\n[2/2] 验证通过!")

    asyncio.run(_test())
