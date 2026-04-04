"""学生 agent 的专用记忆."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from schemas.student import StudentAttitude, StudentLevel, StudentProfile


@dataclass
class StudentAgentMemory:
    """学生 agent 的专用记忆（持久化到数据库）."""

    name: str = ""
    level: StudentLevel = StudentLevel.AVERAGE
    attitude: StudentAttitude = StudentAttitude.NEUTRAL
    learning_ability: int = 5

    learned_concepts: list[str] = field(default_factory=list)
    confused_points: list[str] = field(default_factory=list)
    questions_asked: list[str] = field(default_factory=list)

    initial_knowledge_level: float = 0.0
    current_knowledge_level: float = 0.0
    learning_rate: float = 0.05

    def __post_init__(self) -> None:
        """初始化后计算学习速率."""
        self.learning_rate = self.learning_ability * 0.01

    @classmethod
    def from_profile(cls, profile: StudentProfile) -> StudentAgentMemory:
        """从 StudentProfile 创建."""
        return cls(
            name=profile.name,
            level=profile.level,
            attitude=profile.attitude,
            learning_ability=profile.learning_ability,
        )

    def should_remember_concept(self, concept: str, rng: random.Random) -> bool:
        """判断是否应该记住这个概念（基于学习参数）."""
        return rng.random() < (self.current_knowledge_level + 0.5)

    def update_knowledge(self, new_concepts: list[str], rng: random.Random) -> None:
        """尝试学习新概念，基于学习参数决定是否记住."""
        for concept in new_concepts:
            if concept in self.learned_concepts:
                continue
            if self.should_remember_concept(concept, rng):
                self.learned_concepts.append(concept)
                self.current_knowledge_level = min(
                    1.0,
                    self.current_knowledge_level + self.learning_rate,
                )

    def get_system_prompt_addition(self, topic: str) -> str:
        """生成学生 system prompt 的附加内容."""
        learned = (
            ", ".join(self.learned_concepts)
            if self.learned_concepts
            else "尚未开始学习"
        )
        return (
            f'你是学生 agent "{self.name}"，正在学习"{topic}"相关内容。\n\n'
            f"已学习内容: {learned}\n"
            f"当前知识掌握度: {self.current_knowledge_level * 100:.0f}%\n\n"
            f"你的学习特征:\n"
            f"- 学习能力: {self.learning_ability}/10\n"
            f"- 学习态度: {self.attitude.value}\n"
            f"- 学习水平: {self.level.value}\n\n"
            f"行为准则:\n"
            f"1. 回答问题时，基于你已学习的内容\n"
            f"2. 如果不确定，可以表示困惑或提问\n"
            f"3. 积极(active)的学生更主动回答问题\n"
            f"4. 你的回答质量应该与当前知识水平相符\n"
        )
