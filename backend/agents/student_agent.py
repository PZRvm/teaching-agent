"""学生 Agent - 负责回答问题和互动."""

from __future__ import annotations

import logging
import random
from datetime import datetime

from agents.memories import SessionMemory, StudentAgentMemory
from core.settings import STUDENT_RESPOND_PROBABILITIES, TIMEZONE
from schemas.message import Message, MessageType
from schemas.student import StudentProfile

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
        probability = STUDENT_RESPOND_PROBABILITIES.get(self.profile.attitude.value, 0.5)
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

        try:
            content = self.llm.invoke(messages)
        except Exception as e:
            logger.error(
                "StudentAgent LLM 调用失败: student=%s, error=%s",
                self.profile.name,
                e,
            )
            raise RuntimeError(f"学生 {self.profile.name} 的 LLM 调用失败: {e}") from e

        if not content or not content.strip():
            logger.warning("StudentAgent LLM 返回空内容: student=%s", self.profile.name)
            content = ""

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
