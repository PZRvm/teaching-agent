"""Agent 记忆管理系统 - 统一导出模块."""

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field

from agents.memories.session_memory import SessionMemory
from agents.memories.student_memory import StudentAgentMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from models.session.schemas import Message, MessageType
from schemas.student import StudentProfile

logger = logging.getLogger(__name__)


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
        elif message.message_type == MessageType.TEACHER_REPLY:
            pass  # 教师回复，已通过 message_history 记录
        elif message.message_type == MessageType.ASSIGN_HOMEWORK:
            pass  # 布置作业，已通过 message_history 记录
        elif message.message_type == MessageType.HOMEWORK_SUBMISSION:
            pass  # 学生提交作业，已通过 message_history 记录
        elif message.message_type == MessageType.HOMEWORK_FEEDBACK:
            pass  # 作业评分，已通过 message_history 记录
        elif message.message_type == MessageType.END_FEEDBACK:
            pass  # 课程结束反馈，已通过 message_history 记录
        elif message.message_type == MessageType.FEEDBACK_SUBMISSION:
            pass  # 学生课程反馈，已通过 message_history 记录

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

    def summarize_checkpoint(self) -> str | None:
        """生成当前检查点的摘要并重置消息历史.

        摘要失败时只丢失叙事上下文，TeacherAgentMemory 的结构化状态不受影响。
        异常不会向上传播，仅记录日志。

        Returns:
            生成的检查点摘要，如果无法生成则返回 None
        """
        messages = self.session_memory.get_recent_messages()
        if not messages:
            self.session_memory.clear_message_history()
            return None

        if self.summary_fn is None:
            self.session_memory.clear_message_history()
            return None

        summary = None
        try:
            prompt = (
                "请将以下课堂对话摘要为一段简洁的教学总结（100字以内）。\n"
                "重点包括：讲授了什么知识点、学生理解情况、发现的误解。\n\n"
                + "\n".join(
                    f"[{m.sender}]: {m.content}" for m in messages
                )
            )
            summary = self.summary_fn(prompt)
            if summary:
                self.session_memory.checkpoint_summaries.append(summary)
        except Exception:
            logger.warning("检查点摘要生成失败，跳过此检查点的摘要", exc_info=True)
        finally:
            # 无论摘要是否成功生成，都清除消息历史
            self.session_memory.clear_message_history()

        return summary


__all__ = [
    "SessionMemory",
    "TeacherAgentMemory",
    "StudentAgentMemory",
    "MemoryManager",
]
