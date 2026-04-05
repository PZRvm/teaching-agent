"""学生 Agent - 负责回答问题和互动."""

from __future__ import annotations

import random

from agents.memories import SessionMemory
from agents.memories.student_memory import StudentAgentMemory
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
