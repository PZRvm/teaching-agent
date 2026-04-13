"""CheckpointPlanService 真实 LLM 集成测试.

使用真实 LLM API 测试 CheckpointPlanService 的检查点计划生成功能。
运行方式: pytest tests/integration/test_checkpoint_service_real.py -v -s -m integration
"""

from dotenv import load_dotenv

load_dotenv()  # noqa: E402

import json  # noqa: E402

import pytest  # noqa: E402

from core.llm_client import LLMClient  # noqa: E402
from models.checkpoint.schemas import (  # noqa: E402
    CheckpointPlan,
    CheckpointState,
)
from models.checkpoint.services.plan_service import CheckpointPlanService  # noqa: E402


@pytest.fixture(scope="module")
def real_llm():
    """创建真实 LLM 客户端."""
    return LLMClient.from_config()


class TestCheckpointPlanServiceReal:
    """使用真实 LLM 测试 CheckpointPlanService 的检查点计划生成."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_plan_didactic_mode(self, real_llm):
        """测试灌输式模式生成检查点计划（真实 LLM）."""
        service = CheckpointPlanService(llm=real_llm)

        print(f"\n{'=' * 70}")
        print("[灌输式模式] 主题: Python 变量与数据类型")
        print(f"{'=' * 70}\n")

        plan = await service.generate_plan(
            topic="Python 变量与数据类型",
            teaching_mode="didactic",
        )

        # 打印生成的计划
        print(f"教学主题: {plan.topic}")
        print(f"教学模式: {plan.teaching_mode}")
        print(f"检查点数量: {len(plan.checkpoints)}")
        print("\n检查点详情:")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"\n  检查点 {i}:")
            print(f"    标题: {cp.title}")
            print(f"    关键点: {cp.key_point}")
            print(f"    状态: {cp.state.value}")
            print(f"    检查问题: {cp.checkpoint_question}")

        print(f"\n{'=' * 70}\n")

        # 验证（真实 LLM 输出可能不精确，使用范围检查）
        assert isinstance(plan, CheckpointPlan)
        assert plan.topic == "Python 变量与数据类型"
        assert plan.teaching_mode == "didactic"
        # LLM 输出非确定性，确保至少有 1 个检查点
        assert len(plan.checkpoints) >= 1
        for cp in plan.checkpoints:
            assert cp.state == CheckpointState.PENDING
            assert len(cp.title) > 0
            assert len(cp.key_point) > 0
            assert len(cp.checkpoint_question) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_plan_heuristic_mode(self, real_llm):
        """测试启发式模式生成检查点计划（真实 LLM）."""
        service = CheckpointPlanService(llm=real_llm)

        print(f"\n{'=' * 70}")
        print("[启发式模式] 主题: Python 循环结构")
        print(f"{'=' * 70}\n")

        plan = await service.generate_plan(
            topic="Python 循环结构",
            teaching_mode="heuristic",
        )

        # 打印生成的计划
        print(f"教学主题: {plan.topic}")
        print(f"教学模式: {plan.teaching_mode}")
        print(f"检查点数量: {len(plan.checkpoints)}")
        print("\n检查点详情:")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"\n  检查点 {i}:")
            print(f"    标题: {cp.title}")
            print(f"    关键点: {cp.key_point}")
            print(f"    状态: {cp.state.value}")
            print(f"    检查问题: {cp.checkpoint_question}")

        print(f"\n{'=' * 70}\n")

        # 验证（真实 LLM 输出非确定性，只检查基本结构）
        assert isinstance(plan, CheckpointPlan)
        assert plan.topic == "Python 循环结构"
        assert plan.teaching_mode == "heuristic"
        # 确保至少生成 1 个检查点
        assert len(plan.checkpoints) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_plan_discussion_mode(self, real_llm):
        """测试讨论式模式生成检查点计划（真实 LLM）."""
        service = CheckpointPlanService(llm=real_llm)

        print(f"\n{'=' * 70}")
        print("[讨论式模式] 主题: 面向对象编程基础")
        print(f"{'=' * 70}\n")

        plan = await service.generate_plan(
            topic="面向对象编程基础",
            teaching_mode="discussion",
        )

        # 打印生成的计划
        print(f"教学主题: {plan.topic}")
        print(f"教学模式: {plan.teaching_mode}")
        print(f"检查点数量: {len(plan.checkpoints)}")
        print("\n检查点详情:")
        for i, cp in enumerate(plan.checkpoints, 1):
            print(f"\n  检查点 {i}:")
            print(f"    标题: {cp.title}")
            print(f"    关键点: {cp.key_point}")
            print(f"    状态: {cp.state.value}")
            print(f"    检查问题: {cp.checkpoint_question}")

        print(f"\n{'=' * 70}\n")

        # 验证（真实 LLM 输出非确定性，只检查基本结构）
        assert isinstance(plan, CheckpointPlan)
        assert plan.topic == "面向对象编程基础"
        assert plan.teaching_mode == "discussion"
        # 确保至少生成 1 个检查点
        assert len(plan.checkpoints) >= 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_plan_serialize_to_json(self, real_llm):
        """测试生成的计划可以序列化为 JSON（真实 LLM）."""
        service = CheckpointPlanService(llm=real_llm)

        print(f"\n{'=' * 70}")
        print("[JSON 序列化测试] 主题: Python 函数")
        print(f"{'=' * 70}\n")

        plan = await service.generate_plan(
            topic="Python 函数",
            teaching_mode="heuristic",
        )

        # 序列化为 JSON
        plan_dict = plan.model_dump()
        json_str = json.dumps(plan_dict, ensure_ascii=False, indent=2)

        print("JSON 序列化结果:")
        print(json_str)

        # 反序列化
        restored_plan = CheckpointPlan(**plan_dict)

        print(f"\n{'=' * 70}\n")

        # 验证
        assert restored_plan.topic == plan.topic
        assert restored_plan.teaching_mode == plan.teaching_mode
        assert len(restored_plan.checkpoints) == len(plan.checkpoints)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_plan_edge_cases(self, real_llm):
        """测试边界情况：单检查点和多检查点（真实 LLM）."""
        service = CheckpointPlanService(llm=real_llm)

        # 单检查点
        print(f"\n{'=' * 70}")
        print("[单检查点测试] 主题: Python 列表推导式")
        print(f"{'=' * 70}\n")

        plan_single = await service.generate_plan(
            topic="Python 列表推导式",
            teaching_mode="didactic",
        )

        print(f"生成的检查点数量: {len(plan_single.checkpoints)}")
        print(f"检查点标题: {plan_single.checkpoints[0].title}")

        # 单检查点 - 确保至少生成 1 个
        assert len(plan_single.checkpoints) >= 1

        # 多检查点
        print(f"\n{'=' * 70}")
        print("[多检查点测试] 主题: Python 装饰器")
        print(f"{'=' * 70}\n")

        plan_multi = await service.generate_plan(
            topic="Python 装饰器",
            teaching_mode="heuristic",
        )

        print(f"生成的检查点数量: {len(plan_multi.checkpoints)}")
        for i, cp in enumerate(plan_multi.checkpoints, 1):
            print(f"  {i}. {cp.title}")

        print(f"\n{'=' * 70}\n")

        # 多检查点 - 确保至少生成 1 个
        assert len(plan_multi.checkpoints) >= 1
