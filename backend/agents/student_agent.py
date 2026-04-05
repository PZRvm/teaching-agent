"""学生 Agent - 负责回答问题和互动."""

from __future__ import annotations

import random
from datetime import datetime

from agents.memories import SessionMemory
from agents.memories.student_memory import StudentAgentMemory
from schemas.message import Message, MessageType
from schemas.student import StudentProfile


class StudentAgent:
    """学生 Agent - 负责回答问题和互动."""

    def __init__(
        self,
        *,
        session_memory: SessionMemory,
        llm,
        profile: StudentProfile,
        memory: StudentAgentMemory | None = None,
        rng: random.Random | None = None,
    ) -> None:
        """初始化学生 Agent.

        Args:
            session_memory: 会话记忆
            llm: LLM 客户端（需实现 invoke(prompt) -> str 接口）
            profile: 学生配置
            memory: 已有的 StudentAgentMemory（可选）
            rng: 随机数生成器（可选，用于测试确定性）
        """
        self.session_memory = session_memory
        self.llm = llm
        self.profile = profile
        self.rng = rng or random.Random()

        self.memory = memory or StudentAgentMemory.from_profile(profile)

    # 态度 → 响应概率
    _RESPOND_PROBABILITIES = {
        "active": 0.8,
        "neutral": 0.5,
        "passive": 0.2,
    }

    def should_respond(self) -> bool:
        """判断学生是否应该响应（基于态度概率）.

        Returns:
            True 表示学生选择响应
        """
        probability = self._RESPOND_PROBABILITIES.get(
            self.profile.attitude.value, 0.5
        )
        return self.rng.random() < probability

    def _build_system_prompt(self) -> str:
        """构建学生 system prompt.

        根据学生的 level 生成角色化提示。
        """
        topic = self.session_memory.topic
        student_context = self.memory.get_system_prompt_addition(topic)
        context = self.session_memory.get_agent_context()

        level_instructions = {
            "excellent": (
                "- 你的回答应该准确、有条理，能举一反三\n"
                "- 你能正确使用专业概念和术语\n"
                "- 你能从多个角度分析问题\n"
            ),
            "average": (
                "- 你的回答基本正确，但可能不够深入\n"
                "- 你对一些概念可能有些模糊\n"
                "- 你能解决基本问题，复杂问题可能出错\n"
            ),
            "basic": (
                "- 你的回答可能不够准确，有时会混淆概念\n"
                "- 你对基础概念的理解不够牢固\n"
                "- 你可能会犯一些常见的错误\n"
            ),
        }

        level_section = level_instructions.get(
            self.profile.level.value, level_instructions["average"]
        )

        return f"""{student_context}

{level_section}
{context}
"""

    def answer_question(self, question: str) -> str:
        """回答教师的问题.

        Args:
            question: 教师提出的问题

        Returns:
            学生的回答文本
        """
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        content = self.llm.invoke(messages)

        message = Message(
            sender=self.profile.name,
            message_type=MessageType.ANSWER_TO_CHECKPOINT,
            content=content,
            timestamp=datetime.now(),
        )
        self.session_memory.add_message(message)

        return content
