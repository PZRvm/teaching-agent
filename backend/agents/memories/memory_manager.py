"""Agent 记忆管理系统."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from schemas.message import Message
from schemas.student import StudentAttitude, StudentLevel, StudentProfile


@dataclass
class SessionMemory:
    """会话级别的记忆管理."""

    session_id: int
    topic: str

    message_history: list[Message] = field(default_factory=list)
    teaching_summary: str = ""

    max_history_messages: int = 50
    summary_update_interval: int = 10
    last_summary_update: int = 0

    def add_message(self, message: Message) -> None:
        """添加消息到历史."""
        self.message_history.append(message)

    def should_update_summary(self) -> bool:
        """判断是否需要更新摘要."""
        return (
            len(self.message_history) - self.last_summary_update
            >= self.summary_update_interval
        )

    def mark_summary_updated(self) -> None:
        """标记摘要已更新."""
        self.last_summary_update = len(self.message_history)

    def get_recent_messages(self) -> list[Message]:
        """获取最近 N 条消息."""
        return self.message_history[-self.max_history_messages :]

    def get_agent_context(self) -> str:
        """获取 agent 完整上下文."""
        recent = self.get_recent_messages()
        parts = [
            f"教学主题: {self.topic}",
            f"教学摘要: {self.teaching_summary}",
            "最近的对话:",
        ]
        for msg in recent:
            parts.append(f"[{msg.sender}] ({msg.message_type.value}): {msg.content}")
        return "\n".join(parts)


@dataclass
class TeacherAgentMemory:
    """教师 agent 的专用记忆."""

    covered_topics: list[str] = field(default_factory=list)
    student_questions: dict[str, list[str]] = field(default_factory=dict)
    student_participation: dict[str, int] = field(default_factory=dict)
    teaching_progress: float = 0.0
    student_misconceptions: dict[str, list[str]] = field(default_factory=dict)

    def record_covered_topic(self, topic: str) -> None:
        """记录已讲授主题，避免重复."""
        if topic not in self.covered_topics:
            self.covered_topics.append(topic)

    def record_student_question(self, student_name: str, question: str) -> None:
        """记录学生提问."""
        if student_name not in self.student_questions:
            self.student_questions[student_name] = []
        self.student_questions[student_name].append(question)

    def record_student_participation(self, student_name: str) -> None:
        """记录学生参与次数."""
        self.student_participation[student_name] = (
            self.student_participation.get(student_name, 0) + 1
        )

    def record_misconception(self, student_name: str, misconception: str) -> None:
        """记录学生误解."""
        if student_name not in self.student_misconceptions:
            self.student_misconceptions[student_name] = []
        self.student_misconceptions[student_name].append(misconception)

    def get_system_prompt_addition(self, topic: str) -> str:
        """生成教师 system prompt 的附加内容."""
        status_lines = []
        for name, count in self.student_participation.items():
            status_lines.append(f"- {name}: 发言{count}次")

        student_status = "\n".join(status_lines) if status_lines else "暂无学生发言记录"

        return (
            f'你是教师 agent，正在教授"{topic}"相关内容。\n\n'
            f"已讲授内容: {', '.join(self.covered_topics) if self.covered_topics else '暂无'}\n"
            f"教学进度: {self.teaching_progress * 100:.0f}%\n\n"
            f"学生参与情况:\n{student_status}\n\n"
            f"重要提醒:\n"
            f"1. 避免重复讲授已覆盖的知识点\n"
            f"2. 根据学生的参与度和理解程度调整教学节奏\n"
            f"3. 对于困惑的学生，提供更详细的解释\n"
        )


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

