"""学生 Agent - 负责回答问题和互动."""

from __future__ import annotations

import logging
import random
from datetime import datetime

from agents.memories import SessionMemory, StudentAgentMemory
from core.llm_utils import safe_llm_call
from core.settings import DEFAULT_RESPOND_PROBABILITY, STUDENT_RESPOND_PROBABILITIES, TIMEZONE
from models.session.schemas import Message, MessageType
from schemas.student import StudentAttitude, StudentProfile

logger = logging.getLogger(__name__)


class StudentAgent:
    """学生 Agent - 负责回答问题和互动."""

    # 水平对应的回答指导
    _LEVEL_INSTRUCTIONS = {
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

    def should_respond(self) -> bool:
        """判断学生是否应该响应（基于态度概率）.

        Returns:
            True 表示学生选择响应
        """
        probability = STUDENT_RESPOND_PROBABILITIES.get(
            self.profile.attitude.value, DEFAULT_RESPOND_PROBABILITY
        )
        return self.rng.random() < probability

    def _build_system_prompt(self) -> str:
        """构建学生 system prompt.

        根据学生的 level 生成角色化提示。
        """
        topic = self.session_memory.topic
        student_context = self.memory.get_system_prompt_addition(topic)
        context = self.session_memory.get_agent_context()

        level_section = self._LEVEL_INSTRUCTIONS.get(
            self.profile.level.value, self._LEVEL_INSTRUCTIONS["average"]
        )

        return f"""{student_context}

{level_section}
{context}
"""

    def _call_llm_and_record(self, user_prompt: str, message_type: MessageType) -> str:
        """调用 LLM 并记录消息到会话记忆.

        Args:
            user_prompt: 用户提示
            message_type: 消息类型

        Returns:
            LLM 响应文本

        Raises:
            RuntimeError: LLM 调用失败时
        """
        system_prompt = self._build_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            f"学生 {self.profile.name}",
            "LLM 调用",
            messages,
        )

        if not content or not content.strip():
            logger.warning("StudentAgent LLM 返回空内容: student=%s", self.profile.name)
            return ""

        message = Message(
            sender=self.profile.name,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(TIMEZONE),
        )
        self.session_memory.add_message(message)

        return content

    def answer_question(self, question: str) -> str:
        """回答教师的问题.

        Args:
            question: 教师提出的问题

        Returns:
            学生的回答文本
        """
        return self._call_llm_and_record(question, MessageType.ANSWER_TO_CHECKPOINT)

    def ask_question(self, teaching_context: str) -> str:
        """基于困惑点向教师提问.

        Args:
            teaching_context: 最近的教学内容上下文（触发提问的原因）

        Returns:
            学生提出的问题
        """
        user_prompt = (
            f"基于以下教学内容，请以学生的身份提出一个你不理解的问题。\n"
            f"教学内容: {teaching_context}\n"
            f"要求: 提问要具体、自然，符合你的学习水平和当前知识掌握程度。"
        )
        return self._call_llm_and_record(user_prompt, MessageType.QUESTION_TO_TEACHER)

    def submit_homework(self, homework_prompt: str) -> str:
        """提交作业.

        Args:
            homework_prompt: 作业题目/要求

        Returns:
            学生的作业回答
        """
        user_prompt = (
            f"请完成以下作业：\n\n{homework_prompt}\n\n"
            f"要求: 根据你已学到的知识完成作业，展示你的解题过程。"
        )
        return self._call_llm_and_record(user_prompt, MessageType.HOMEWORK_SUBMISSION)

    def give_feedback(self) -> str:
        """对课程给出总结性反馈.

        Returns:
            学生的课程反馈文本
        """
        user_prompt = (
            "课程即将结束，请对今天的学习进行总结和反馈。\n"
            "请包含以下内容：\n"
            "1. 你学到了什么\n"
            "2. 你还有什么不理解的地方\n"
            "3. 你对课程的感受\n\n"
            "要求: 以自然的学生口吻回答，内容符合你的学习水平。"
        )
        return self._call_llm_and_record(user_prompt, MessageType.FEEDBACK_SUBMISSION)

    def update_knowledge(self) -> None:
        """旁听学习 - 从对话中学习新概念（概率性）.

        旁听学习的触发条件：
        - 学生没有参与当前对话
        - 基于态度和学习能力决定是否学习

        流程：
        1. 根据态度和学习能力计算学习概率
        2. 概率性决定是否学习
        3. 如果学习，从会话记忆中提取概念并更新学生记忆
        """
        # 计算学习概率（态度积极 + 学习能力强 = 更高概率）
        # 基础概率 50%，态度影响 ±20%，学习能力影响 ±30%
        base_probability = 0.5
        attitude_bonus = {
            StudentAttitude.ACTIVE: 0.2,
            StudentAttitude.NEUTRAL: 0.0,
            StudentAttitude.PASSIVE: -0.1,
        }.get(self.profile.attitude, 0.0)
        learning_ability_bonus = (self.profile.learning_ability - 5) * 0.06  # -0.3 to +0.3

        learn_probability = base_probability + attitude_bonus + learning_ability_bonus
        learn_probability = max(0.0, min(1.0, learn_probability))

        # 决定是否学习
        if self.rng.random() >= learn_probability:
            return  # 学生这次没有学到东西

        # 从会话记忆中提取最近的讲授内容作为"概念"
        # 收集所有 lecture 消息的内容作为潜在概念
        lecture_messages = [
            m for m in self.session_memory.message_history
            if m.message_type == MessageType.LECTURE
        ]

        # 提取概念（简化版：将每个 lecture 消息视为一个"概念"）
        # TODO: 未来可以使用 LLM 提取关键概念
        new_concepts = [f"讲授: {msg.content[:50]}..." for msg in lecture_messages[-3:]]  # 最近3条

        if not new_concepts:
            return  # 没有可学的内容

        # 更新学生记忆
        self.memory.update_knowledge(new_concepts, self.rng)
