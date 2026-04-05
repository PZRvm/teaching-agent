"""CheckpointPlanService 单元测试."""

import pytest
from pydantic import ValidationError

from models.checkpoint.schemas import (
    Checkpoint,
    CheckpointPlan,
)
from models.checkpoint.service import CheckpointPlanService


@pytest.mark.asyncio
class TestCheckpointPlanService:
    """CheckpointPlanService 单元测试."""

    async def test_generate_plan_with_structured_output(self, mock_llm_with_structured_output):
        """使用 structured output 生成检查点计划."""
        mock_llm_with_structured_output.ainvoke.return_value = CheckpointPlan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title="变量与数据类型",
                    key_point="int, float, str, bool",
                    checkpoint_question="Python 有哪些基本数据类型?",
                ),
            ],
        )

        service = CheckpointPlanService(mock_llm_with_structured_output)
        plan = await service.generate_plan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoint_count=3,
        )

        assert plan.topic == "Python 基础入门"
        assert len(plan.checkpoints) == 1
        assert plan.checkpoints[0].title == "变量与数据类型"

    async def test_generate_plan_fallback_to_json_parsing(self, mock_llm_without_structured_output):
        """Structured output 失败时，fallback 到手动 JSON 解析."""
        # 模拟 structured output 失败，返回 JSON 字符串
        mock_llm_without_structured_output.ainvoke.side_effect = [
            # 第一次调用 structured output 失败
            Exception("Structured output not supported"),
            # 第二次调用返回 JSON 字符串
            """```json
{
  "topic": "Python 基础入门",
  "teaching_mode": "heuristic",
  "checkpoints": [
    {
      "title": "变量与数据类型",
      "key_point":int, float, str",
      "checkpoint_question": "Python 有哪些基本数据类型?"
    }
  ]
}
```""",
        ]

        service = CheckpointPlanService(mock_llm_without_structured_output)
        plan = await service.generate_plan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoint_count=3,
        )

        assert plan.topic == "Python 基础入门"
        assert len(plan.checkpoints) == 1

    async def test_generate_plan_fallback_to_single_checkpoint(self, mock_llm_json_parse_fails):
        """JSON 解析也失败时，fallback 到单个检查点."""
        # 两次 fallback 都失败，返回单个检查点的兜底方案
        mock_llm_json_parse_fails.ainvoke.side_effect = [
            Exception("Structured output not supported"),
            "Invalid JSON response",
        ]

        service = CheckpointPlanService(mock_llm_json_parse_fails)
        plan = await service.generate_plan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoint_count=3,
        )

        # 返回单个检查点的兜底计划
        assert len(plan.checkpoints) == 1
        assert plan.checkpoints[0].title == "知识点讲解"

    async def test_generate_plan_validates_teaching_mode(self, mock_llm_with_structured_output):
        """生成计划时验证教学模式 - LLM 返回无效模式时应失败."""
        # 模拟 LLM 返回无效的 JSON (包含无效教学模式，但检查点有效)
        mock_llm_with_structured_output.ainvoke.return_value = """{
  "topic": "Python 基础入门",
  "teaching_mode": "invalid_mode",
  "checkpoints": [
    {
      "title": "测试",
      "key_point": "测试知识点",
      "checkpoint_question": "测试问题"
    }
  ]
}"""

        service = CheckpointPlanService(mock_llm_with_structured_output)

        # 应该抛出 ValidationError
        with pytest.raises(ValidationError, match="teaching_mode"):
            await service.generate_plan(
                topic="Python 基础入门",
                teaching_mode="heuristic",
                checkpoint_count=3,
            )

    async def test_build_prompt_includes_topic_and_mode(self):
        """验证生成的 prompt 包含主题和教学模式."""
        from unittest.mock import MagicMock

        mock_llm = MagicMock()
        service = CheckpointPlanService(mock_llm)

        prompt = service._build_prompt("Python 基础入门", "heuristic", 3)

        # 验证 prompt 包含关键信息
        assert "Python 基础入门" in prompt
        assert "heuristic" in prompt
        assert "3" in prompt
        assert "检查点" in prompt

    async def test_load_mode_instructions(self):
        """验证加载教学模式指令."""
        service = CheckpointPlanService(None)

        heuristic_instruction = service._load_mode_instructions("heuristic")
        assert "启发式" in heuristic_instruction
        assert "检查点问题" in heuristic_instruction

        didactic_instruction = service._load_mode_instructions("didactic")
        assert "灌输式" in didactic_instruction

        # 无效模式应返回默认指令
        default_instruction = service._load_mode_instructions("invalid")
        assert "检查点" in default_instruction

    async def test_generate_plan_honors_checkpoint_count(self, mock_llm_with_structured_output):
        """生成计划时遵守指定的检查点数量."""
        mock_llm_with_structured_output.ainvoke.return_value = CheckpointPlan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoints=[
                Checkpoint(
                    title=f"检查点 {i}",
                    key_point=f"知识点 {i}",
                    checkpoint_question=f"问题 {i}?",
                )
                for i in range(5)
            ],
        )

        service = CheckpointPlanService(mock_llm_with_structured_output)
        plan = await service.generate_plan(
            topic="Python 基础入门",
            teaching_mode="heuristic",
            checkpoint_count=5,
        )

        assert len(plan.checkpoints) == 5

    async def test_parse_json_handles_markdown_code_blocks(self):
        """验证 JSON 解析能处理 Markdown 代码块."""
        service = CheckpointPlanService(None)

        json_str = """
```json
{
  "topic": "Python 基础入门",
  "teaching_mode": "heuristic",
  "checkpoints": []
}
```
"""
        result = service._parse_json(json_str)
        assert result["topic"] == "Python 基础入门"

    async def test_parse_json_handles_plain_json(self):
        """验证 JSON 解析能处理纯 JSON."""
        service = CheckpointPlanService(None)

        json_str = '{"topic": "Python 基础入门", "checkpoints": []}'
        result = service._parse_json(json_str)
        assert result["topic"] == "Python 基础入门"
