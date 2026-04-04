"""Agent 记忆管理系统 - 统一导出模块."""

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from agents.memories.session_memory import SessionMemory
from agents.memories.student_memory import StudentAgentMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from schemas.message import Message, MessageType
from schemas.student import StudentProfile


@dataclass
class MemoryManager:
    """记忆管理器 - 负责更新和维持 agent 记忆."""

    session_memory: SessionMemory
    teacher_memory: TeacherAgentMemory = field(default_factory=TeacherAgentMemory)
    student_memories: dict[str, StudentAgentMemory] = field(default_factory=dict)

    # 可注入的 LLM 调用函数
    extract_knowledge_fn: Callable[[str], list[str]] | None = None
    summary_fn: Callable[[str], str] | None = None
    summary_update_interval: int = 10

    # 用于学生记忆判断的随机数生成器
    student_rng: random.Random = field(default_factory=lambda: random.Random())

    def __post_init__(self) -> None:
        """初始化后同步配置."""
        self.session_memory.summary_update_interval = self.summary_update_interval

    def register_student(self, profile: StudentProfile) -> None:
        """注册学生到记忆系统."""
        self.student_memories[profile.name] = StudentAgentMemory.from_profile(profile)

    def process_message(self, message: "Message") -> None:
        """处理新消息并更新记忆."""
        self.session_memory.add_message(message)

        if message.message_type == MessageType.LECTURE:
            self._process_lecture(message)
        elif message.message_type == MessageType.CHECKPOINT_QUESTION:
            pass  # 教师提问，暂不特殊处理
        elif message.message_type == MessageType.REPLY_TO_TEACHER:
            self._process_reply_to_teacher(message)
        elif message.message_type == MessageType.QUESTION_TO_TEACHER:
            self._process_question_to_teacher(message)
        elif message.message_type == MessageType.ANSWER_TO_CHECKPOINT:
            self._process_answer_to_checkpoint(message)

        self._check_and_update_summary()

    def _process_lecture(self, message: "Message") -> None:
        """处理教师讲授内容."""
        if self.extract_knowledge_fn:
            knowledge_points = self.extract_knowledge_fn(message.content)
        else:
            knowledge_points = []

        for kp in knowledge_points:
            self.teacher_memory.record_covered_topic(kp)

        for _name, student_mem in self.student_memories.items():
            student_mem.update_knowledge(knowledge_points, self.student_rng)

    def _process_reply_to_teacher(self, message: "Message") -> None:
        """处理学生回答教师."""
        self.teacher_memory.record_student_participation(message.sender)

    def _process_question_to_teacher(self, message: "Message") -> None:
        """处理学生向教师提问."""
        self.teacher_memory.record_student_question(message.sender, message.content)

    def _process_answer_to_checkpoint(self, message: "Message") -> None:
        """处理学生回答 checkpoint 问题."""
        self.teacher_memory.record_student_participation(message.sender)

    def _check_and_update_summary(self) -> None:
        """检查并更新教学摘要."""
        if not self.session_memory.should_update_summary():
            return
        if self.summary_fn is None:
            return

        recent = self.session_memory.get_recent_messages()
        message_text = "\n".join(
            f"[{m.sender}] ({m.message_type.value}): {m.content}" for m in recent
        )
        prompt = (
            f"请总结以下教学对话，提炼关键教学内容：\n\n"
            f"教学主题: {self.session_memory.topic}\n\n"
            f"最近对话:\n{message_text}\n\n"
            f"请提供:\n"
            f"1. 已讲授的主要知识点（3-5个）\n"
            f"2. 学生普遍掌握的内容\n"
            f"3. 学生普遍困惑的内容（如有）\n"
            f"4. 下一步教学建议\n\n"
            f"摘要格式：简洁明了，便于 agent 理解当前教学状态。"
        )

        self.session_memory.teaching_summary = self.summary_fn(prompt)
        self.session_memory.mark_summary_updated()


__all__ = [
    "SessionMemory",
    "TeacherAgentMemory",
    "StudentAgentMemory",
    "MemoryManager",
]
