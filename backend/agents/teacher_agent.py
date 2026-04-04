"""教师 Agent - 负责讲授内容生成和教学控制."""

from __future__ import annotations

from datetime import datetime

from agents.memories import SessionMemory
from agents.memories.memory_manager import MemoryManager
from schemas.message import Message, MessageType
from schemas.student import StudentProfile

VALID_TEACHING_MODES = ("didactic", "heuristic", "discussion")


class TeacherAgent:
    """教师 Agent - 负责讲授内容生成和教学控制."""

    def __init__(
        self,
        *,
        session_memory: SessionMemory,
        llm,
        teaching_mode: str = "didactic",
        students: list[StudentProfile] | None = None,
        memory_manager: MemoryManager | None = None,
    ) -> None:
        """初始化教师 Agent.

        Args:
            session_memory: 会话记忆
            llm: LLM 客户端（需实现 invoke(prompt) -> str 接口）
            teaching_mode: 教学模式（didactic/heuristic/discussion）
            students: 学生配置列表
            memory_manager: 已有的 MemoryManager（可选）

        Raises:
            ValueError: teaching_mode 不在有效范围内
        """
        if teaching_mode not in VALID_TEACHING_MODES:
            raise ValueError(
                f"无效的教学模式: {teaching_mode}，"
                f"有效值为: {', '.join(VALID_TEACHING_MODES)}"
            )

        self.session_memory = session_memory
        self.teaching_mode = teaching_mode
        self.llm = llm

        if memory_manager is not None:
            self.memory_manager = memory_manager
        else:
            self.memory_manager = MemoryManager(session_memory=session_memory)

        # 注册学生
        if students:
            for profile in students:
                self.memory_manager.register_student(profile)

    def _build_system_prompt(self) -> str:
        """构建教师 system prompt.

        根据教学模式生成不同的系统提示。
        """
        topic = self.session_memory.topic
        context = self.memory_manager.session_memory.get_agent_context()
        teacher_context = self.memory_manager.teacher_memory.get_system_prompt_addition(
            topic=topic
        )

        mode_instructions = {
            "didactic": (
                "## 教学模式：灌输式\n"
                "- 以知识点讲解为主，连续讲授，不主动提问\n"
                "- 专注于清晰、系统地传授知识\n"
                "- 确保内容覆盖教学主题的所有关键知识点\n"
                "- 使用具体示例和类比帮助理解\n"
            ),
            "heuristic": (
                "## 教学模式：启发式\n"
                "- 结合案例教学，在讲授中穿插互动环节\n"
                "- 每讲授3-5个知识点后，提出一个 checkpoint 问题\n"
                "- 鼓励学生思考和回答\n"
                "- 根据学生回答情况调整讲解节奏\n"
            ),
            "discussion": (
                "## 教学模式：讨论式\n"
                "- 频繁提问，每1-2个知识点后引导一次讨论\n"
                "- 鼓励学生积极参与讨论和表达观点\n"
                "- 引导学生通过讨论深化理解\n"
                "- 对学生的观点给予反馈和补充\n"
            ),
        }

        mode_section = mode_instructions.get(
            self.teaching_mode, mode_instructions["didactic"]
        )

        return f"""你是教师 agent，正在教授"{topic}"相关内容。

## 基本信息
- 教学主题: {topic}
- 教学模式: {self.teaching_mode}

{mode_section}

{teacher_context}

## 重要提醒
1. 避免重复讲授已覆盖的知识点
2. 根据学生的参与度和理解程度调整教学节奏
3. 对于困惑的学生，提供更详细的解释
4. 每次讲授一个完整的知识点段，不要太长也不要太短
5. 使用通俗易懂的语言，适当使用类比和实例

{context}
"""

    def _build_lecture_messages(self) -> list[dict]:
        """构建讲授消息列表."""
        system_prompt = self._build_system_prompt()
        user_prompt = f"请继续讲授关于「{self.session_memory.topic}」的内容。"
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _record_lecture(self, content: str) -> None:
        """通过 MemoryManager 记录讲授消息."""
        message = Message(
            sender="teacher",
            message_type=MessageType.LECTURE,
            content=content,
            timestamp=datetime.now(),
        )
        self.memory_manager.process_message(message)

    def deliver_lecture(self) -> str:
        """生成讲授内容.

        Returns:
            讲授内容文本
        """
        messages = self._build_lecture_messages()

        content = self.llm.invoke(messages, temperature=self._get_mode_temperature())
        self._record_lecture(content)

        return content

    def deliver_lecture_stream(self):
        """流式生成讲授内容，逐 token 输出.

        Yields:
            每个文本 chunk
        """
        messages = self._build_lecture_messages()

        full_content = []
        for chunk in self.llm.stream(messages, temperature=self._get_mode_temperature()):
            full_content.append(chunk)
            yield chunk

        content = "".join(full_content)
        self._record_lecture(content)

    def _get_mode_temperature(self) -> float:
        """根据教学模式获取合适的温度值.

        Returns:
            温度值
        """
        temperatures = {
            "didactic": 0.3,
            "heuristic": 0.5,
            "discussion": 0.7,
        }
        return temperatures.get(self.teaching_mode, 0.3)

    def is_content_complete(self) -> bool:
        """判断教学内容是否已完成.

        通过 LLM 判断已讲授的知识点是否覆盖了教学主题。

        Returns:
            True if teaching content is complete
        """
        topic = self.session_memory.topic
        covered = self.memory_manager.teacher_memory.covered_topics

        if not covered:
            return False

        prompt = (
            f"判断以下已讲授的知识点是否完整覆盖了「{topic}」"
            f"这个教学主题的核心内容。\n\n"
            f"已讲授的知识点:\n"
            + "\n".join(f"- {kp}" for kp in covered)
            + "\n\n请只回答「完成」或「未完成」。"
        )

        response = self.llm.invoke(prompt, temperature=0.1)
        return response.strip() == "完成"
