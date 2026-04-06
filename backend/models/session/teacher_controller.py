"""TeacherSessionController - 教师模式核心控制器."""

from datetime import datetime

from collections.abc import Callable
from typing import Optional

from agents.student_agent import StudentAgent
from agents.memories.memory_manager import MemoryManager
from models.checkpoint.schemas import CheckpointPlan
from models.session.schemas import Message, MessageType


class TeacherSessionController:
    """教师模式手动教学流程控制器.

    用户扮演教师角色，通过 WebSocket 命令控制教学流程。
    支持检查点驱动的手动教学，用户可编辑检查点、手动推进、控制对话节奏。

    核心特性：
    - 无 TeacherAgent（用户提供教学内容）
    - 至少一轮对话约束（与观察模式相同）
    - 旁听学习机制（复用观察模式逻辑）
    - 检查点手动推进（强制结束当前对话）
    """

    def __init__(
        self,
        *,
        student_agents: list[StudentAgent],
        memory_manager: MemoryManager,
        checkpoint_plan: CheckpointPlan,
        ws_push_callback: Optional[Callable] = None,
    ):
        """初始化教师模式控制器.

        Args:
            student_agents: 学生 agent 列表
            memory_manager: 记忆管理器
            checkpoint_plan: 检查点计划
            ws_push_callback: WebSocket 推送回调（用于测试）
        """
        self.student_agents = student_agents
        self.memory_manager = memory_manager
        self.checkpoint_plan = checkpoint_plan
        self._ws_push_callback = ws_push_callback

        # 对话状态追踪
        self._active_dialogue: Optional[dict] = None  # 当前活跃对话 {student_name: round_count}
        self._dialogue_round_count: int = 0  # 当前对话轮数

    def handle_broadcast_lecture(self, content: str) -> None:
        """处理用户广播讲授内容.

        Args:
            content: 用户（教师）提供的讲授内容

        流程：
            1. 记录 lecture 消息到 SessionMemory
            2. 推送 WebSocket 事件（可选）
        """
        message = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content=content,
            receiver="all",
            timestamp=datetime.now(),
        )

        self.memory_manager.session_memory.message_history.append(message)

    def handle_ask_to_all(self, question: str) -> None:
        """向全体学生提问并收集回答.

        Args:
            question: 教师提出的问题

        流程：
            1. 记录 checkpoint_question 消息到 SessionMemory
            2. 遍历所有学生，调用 ask_question() 收集回答
            3. 记录每个学生的 answer_to_checkpoint 消息
        """
        # 记录教师提问
        question_message = Message(
            sender="teacher",
            message_type=MessageType.CHECKPOINT_QUESTION,
            content=question,
            receiver="all",
            timestamp=datetime.now(),
        )
        self.memory_manager.session_memory.message_history.append(question_message)

        # 收集所有学生的回答
        for student in self.student_agents:
            answer = student.ask_question(question)
            answer_message = Message(
                sender=student.name,
                message_type=MessageType.ANSWER_TO_CHECKPOINT,
                content=answer,
                receiver="teacher",
                timestamp=datetime.now(),
            )
            self.memory_manager.session_memory.message_history.append(answer_message)

    def handle_ask_to_student(self, question: str, student_name: str) -> None:
        """向单个学生提问并收集回答.

        Args:
            question: 教师提出的问题
            student_name: 目标学生名称

        流程：
            1. 记录 checkpoint_question 消息到 SessionMemory（发送给特定学生）
            2. 找到目标学生并调用 ask_question() 收集回答
            3. 记录学生的 answer_to_checkpoint 消息
        """
        # 记录教师提问（发送给特定学生）
        question_message = Message(
            sender="teacher",
            message_type=MessageType.CHECKPOINT_QUESTION,
            content=question,
            receiver=student_name,
            timestamp=datetime.now(),
        )
        self.memory_manager.session_memory.message_history.append(question_message)

        # 找到目标学生并收集回答
        target_student = None
        for student in self.student_agents:
            if student.name == student_name:
                target_student = student
                break

        if target_student is not None:
            answer = target_student.ask_question(question)
            answer_message = Message(
                sender=student_name,
                message_type=MessageType.ANSWER_TO_CHECKPOINT,
                content=answer,
                receiver="teacher",
                timestamp=datetime.now(),
            )
            self.memory_manager.session_memory.message_history.append(answer_message)
