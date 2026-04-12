"""Checkpoint 计划生成服务."""

from models.checkpoint.schemas import Checkpoint, CheckpointPlan


class CheckpointPlanService:
    """检查点计划生成服务.

    使用 LLM 生成检查点计划，支持三层降级策略：
    1. 使用 structured output 直接生成 CheckpointPlan
    2. 降级到手动 JSON 解析
    3. 降级到单个检查点的兜底方案
    """

    def __init__(self, llm):
        """初始化服务.

        Args:
            llm: LangChain ChatModel 实例
        """
        self.llm = llm

    async def generate_plan(
        self, topic: str, teaching_mode: str
    ) -> CheckpointPlan:
        """生成检查点计划.

        Args:
            topic: 教学主题
            teaching_mode: 教学模式 (didactic/heuristic/discussion/teacher)

        Returns:
            生成的检查点计划

        Raises:
            ValidationError: 当 LLM 返回的数据无法通过验证时
        """
        from pydantic import ValidationError as PydanticValidationError

        prompt = self._build_prompt(topic, teaching_mode)

        try:
            # 尝试使用 structured output
            response = await self.llm.ainvoke(prompt)
            # 处理可能不是 CheckpointPlan 的响应
            if isinstance(response, CheckpointPlan):
                return response
            # 如果返回的是字符串，尝试 JSON 解析
            if isinstance(response, str):
                plan_data = self._parse_json(response)
                return CheckpointPlan.model_validate(plan_data)
            # 如果是其他类型，尝试序列化后解析
            plan_data = self._parse_json(str(response))
            return CheckpointPlan.model_validate(plan_data)
        except PydanticValidationError:
            # 重新抛出验证错误 - LLM 返回的数据无效
            raise
        except Exception:
            # 如果 structured output 失败，尝试 JSON 解析
            try:
                response = await self.llm.ainvoke(prompt)
                plan_data = self._parse_json(str(response))
                return CheckpointPlan.model_validate(plan_data)
            except PydanticValidationError:
                # 重新抛出验证错误
                raise
            except Exception:
                # 最后的兜底方案：单个检查点
                return self._create_fallback_plan(topic, teaching_mode)

    def _build_prompt(self, topic: str, teaching_mode: str) -> str:
        """构建 LLM prompt.

        Args:
            topic: 教学主题
            teaching_mode: 教学模式

        Returns:
            完整的 prompt 字符串
        """
        mode_instruction = self._load_mode_instructions(teaching_mode)

        return f"""请为主题 "{topic}" 生成一个教学计划。

请根据主题的复杂度和知识量，自行决定需要多少个检查点。
要求:
- 每个检查点涵盖一个核心知识点
- 检查点数量最多 10 个
- 简单主题 3-5 个，复杂主题 5-8 个

教学模式: {teaching_mode}
{mode_instruction}

请返回一个 JSON 对象，格式如下:
{{
  "topic": "{topic}",
  "teaching_mode": "{teaching_mode}",
  "checkpoints": [
    {{
      "title": "检查点标题",
      "key_point": "核心知识点",
      "checkpoint_question": "检查理解的问题"
    }}
  ]
}}

注意:
- 每个 checkpoint 只包含一个 key_point (字符串)
- 不需要 examples 字段
- checkpoint_question 用于检查学生理解
"""

    def _load_mode_instructions(self, teaching_mode: str) -> str:
        """加载教学模式指令.

        Args:
            teaching_mode: 教学模式

        Returns:
            模式指令字符串
        """
        instructions = {
            "didactic": "灌输式教学：以教师讲解为主，学生被动接受。检查点用于验证基本理解。",
            "heuristic": "启发式教学：教师引导思考，通过检查点问题激发学生思考。",
            "discussion": "讨论式教学：频繁互动，检查点问题引发深入讨论。",
            "teacher": "教师演示模式：教师展示解题过程，检查点验证学生掌握程度。",
        }
        return instructions.get(teaching_mode, "请根据教学模式设计合适的检查点。")

    def _parse_json(self, json_str: str) -> dict:
        """解析 JSON 字符串，支持 Markdown 代码块。

        Args:
            json_str: JSON 字符串

        Returns:
            解析后的字典
        """
        import json
        import re

        # 移除 Markdown 代码块标记
        json_str = re.sub(r"```json\s*", "", json_str)
        json_str = re.sub(r"```\s*$", "", json_str)
        json_str = json_str.strip()

        return json.loads(json_str)

    def _create_fallback_plan(self, topic: str, teaching_mode: str) -> CheckpointPlan:
        """创建兜底检查点计划（单个检查点）.

        Args:
            topic: 教学主题
            teaching_mode: 教学模式

        Returns:
            兜底检查点计划
        """
        return CheckpointPlan(
            topic=topic,
            teaching_mode=teaching_mode,
            checkpoints=[
                Checkpoint(
                    title="知识点讲解",
                    key_point=f"{topic} 的核心概念",
                    checkpoint_question=f"你对 {topic} 有什么疑问吗？",
                )
            ],
        )
