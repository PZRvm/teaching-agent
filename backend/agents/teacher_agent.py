"""教师 Agent - 负责讲授内容生成和教学控制."""

from __future__ import annotations

from datetime import datetime

from agents.memories import SessionMemory
from agents.memories.memory_manager import MemoryManager
from core.llm_utils import safe_llm_call
from core.settings import (
    CONTENT_JUDGE_TEMPERATURE,
    DEFAULT_TEACHING_TEMPERATURE,
    TEACHING_TEMPERATURES,
    TIMEZONE,
)
from models.session.schemas import Message, MessageType
from schemas.student import StudentProfile

VALID_TEACHING_MODES = ("didactic", "heuristic", "discussion")


class TeacherAgent:
    """教师 Agent - 负责讲授内容生成和教学控制."""

    _MODE_INSTRUCTIONS = {
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
                f"无效的教学模式: {teaching_mode}，有效值为: {', '.join(VALID_TEACHING_MODES)}"
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
        teacher_context = self.memory_manager.teacher_memory.get_system_prompt_addition(topic=topic)

        mode_section = self._MODE_INSTRUCTIONS.get(
            self.teaching_mode, self._MODE_INSTRUCTIONS["didactic"]
        )

        return f"""你是教师 agent，正在教授"{topic}"相关内容。

## 基本信息
- 教学主题: {topic}
- 教学模式: {self.teaching_mode}

{mode_section}

{teacher_context}

## 重要提醒
1. **你必须使用中文进行所有教学和交流**
2. 避免重复讲授已覆盖的知识点
3. 根据学生的参与度和理解程度调整教学节奏
4. 对于困惑的学生，提供更详细的解释
5. 每次讲授一个完整的知识点段，不要太长也不要太短
6. 使用通俗易懂的语言，适当使用类比和实例

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

    def _record_message(self, content: str, message_type: MessageType) -> None:
        """通过 MemoryManager 记录消息."""
        message = Message(
            sender="teacher",
            message_type=message_type,
            content=content,
            timestamp=datetime.now(TIMEZONE),
        )
        self.memory_manager.process_message(message)

    def _record_lecture(self, content: str) -> None:
        """通过 MemoryManager 记录讲授消息."""
        self._record_message(content, MessageType.LECTURE)

    def deliver_lecture(self) -> str:
        """生成讲授内容.

        Returns:
            讲授内容文本

        Raises:
            RuntimeError: LLM 调用失败时
        """
        messages = self._build_lecture_messages()

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "讲授",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师讲授 LLM 返回空内容")

        self._record_lecture(content)

        return content

    def deliver_lecture_stream(self):
        """流式生成讲授内容，逐 token 输出.

        Yields:
            每个文本 chunk

        Raises:
            RuntimeError: LLM 调用失败时
        """
        messages = self._build_lecture_messages()

        full_content = []
        try:
            for chunk in self.llm.stream(messages, temperature=self._get_mode_temperature()):
                full_content.append(chunk)
                yield chunk
            content = "".join(full_content)
            if content:
                self._record_lecture(content)
        except Exception as e:
            raise RuntimeError(f"教师讲授的 LLM stream 调用失败: {e}") from e

    def _get_mode_temperature(self) -> float:
        """根据教学模式获取合适的温度值.

        Returns:
            温度值
        """
        return TEACHING_TEMPERATURES.get(self.teaching_mode, DEFAULT_TEACHING_TEMPERATURE)

    def ask_checkpoint_question(self) -> str:
        """提出 checkpoint 问题（启发式模式）.

        基于已讲授的知识点生成一个检查理解程度的问题。

        Returns:
            问题文本

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()
        covered = self.memory_manager.teacher_memory.covered_topics
        recent_topics = covered[-5:] if covered else []
        topics_str = "、".join(recent_topics) if recent_topics else self.session_memory.topic

        user_prompt = (
            f"基于刚才讲授的内容，请提出一个 checkpoint 问题来检查学生的理解程度。\n"
            f"最近讲授的知识点: {topics_str}\n"
            f"要求: 问题应该紧扣已讲授内容，难度适中。只输出问题本身。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "checkpoint 提问",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师 checkpoint 提问 LLM 返回空内容")

        self._record_message(content, MessageType.CHECKPOINT_QUESTION)
        return content

    def ask_discussion_question(self) -> str:
        """提出讨论问题（讨论式模式）.

        基于当前教学内容引导开放性讨论。

        Returns:
            问题文本

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"请基于当前教学内容「{self.session_memory.topic}」提出一个开放性的讨论问题。\n"
            f"要求:\n"
            f"- 问题应该能引发学生思考和讨论\n"
            f"- 鼓励学生表达自己的观点\n"
            f"- 可以结合实际案例或应用场景\n"
            f"只输出问题本身。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "讨论提问",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师讨论提问 LLM 返回空内容")

        self._record_message(content, MessageType.CHECKPOINT_QUESTION)
        return content

    def reply_to_student(self, student_name: str, student_message: str) -> str:
        """回复学生的回答或提问.

        Args:
            student_name: 学生名字
            student_message: 学生的回答或提问内容

        Returns:
            教师的回复内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()

        user_prompt = (
            f"学生「{student_name}」说：{student_message}\n\n请对这位学生的回答/提问给予反馈。"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "回复学生",
            messages,
            temperature=self._get_mode_temperature(),
        )

        if not content or not content.strip():
            raise RuntimeError("教师回复学生 LLM 返回空内容")

        self._record_message(content, MessageType.TEACHER_REPLY)
        return content

    def assign_homework(self) -> str:
        """布置课后作业.

        基于已讲授的内容生成作业题目。

        Returns:
            作业内容文本

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_system_prompt()
        covered = self.memory_manager.teacher_memory.covered_topics
        topics_str = "、".join(covered) if covered else self.session_memory.topic

        user_prompt = (
            f"请基于以下已讲授内容布置一份课后作业。\n"
            f"教学主题: {self.session_memory.topic}\n"
            f"已讲授的知识点: {topics_str}\n\n"
            f"要求:\n"
            f"- 作业应涵盖主要知识点\n"
            f"- 包含基础题和提高题\n"
            f"- 明确答题要求"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "布置作业",
            messages,
            temperature=DEFAULT_TEACHING_TEMPERATURE,
        )

        if not content or not content.strip():
            raise RuntimeError("教师布置作业 LLM 返回空内容")

        self._record_message(content, MessageType.ASSIGN_HOMEWORK)
        return content

    def _build_homework_grading_context(self, student_name: str) -> str:
        """构建作业评分的轻量级上下文.

        与 _build_system_prompt() 不同，这个方法不包含完整的对话历史，
        避免在多学生课堂中 prompt 过长超过上下文窗口限制。

        Args:
            student_name: 学生名字

        Returns:
            轻量级的上下文字符串
        """
        topic = self.session_memory.topic

        # 获取学生记忆（如果存在）
        student_memory = self.memory_manager.student_memories.get(student_name)
        if student_memory:
            learned_count = len(student_memory.learned_concepts)
            student_info = f"该学生已学会 {learned_count} 个知识点"
        else:
            student_info = "新学生，无学习记录"

        # 获取教学摘要（如果存在）
        summary = self.session_memory.teaching_summary or "暂无"

        # 获取教师记忆中的参与度信息
        participation_count = self.memory_manager.teacher_memory.student_participation.get(
            student_name, 0
        )

        return f"""你是教师，正在批改学生"{topic}"相关课程的作业。

## 课程信息
- 教学主题: {topic}
- 教学摘要: {summary}
- 学生参与度: {participation_count} 次课堂互动

## 学生信息
- 学生姓名: {student_name}
- {student_info}

## 评分标准
1. 优秀（90-100分）：完全理解知识点，应用能力强，代码规范
2. 良好（75-89分）：理解较好，基本正确，有小错误
3. 及格（60-74分）：基本理解，有一些错误和不足
4. 不及格（<60分）：理解不足，有重大错误

请客观、公正地评价学生的作业。
"""

    def grade_homework(self, student_name: str, homework_content: str) -> str:
        """评价学生的作业.

        使用 LLM 评价学生提交的作业。

        Args:
            student_name: 学生名字
            homework_content: 学生提交的作业内容

        Returns:
            评价内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        # 使用轻量级上下文，避免包含完整对话历史导致超限
        system_prompt = self._build_homework_grading_context(student_name)

        user_prompt = (
            f"请评价以下学生提交的作业。\n\n"
            f"学生: {student_name}\n"
            f"作业内容:\n{homework_content}\n\n"
            f"请给出:\n"
            f"1. 评分（优秀/良好/及格/不及格）\n"
            f"2. 优点\n"
            f"3. 需要改进的地方"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "作业评分",
            messages,
            temperature=CONTENT_JUDGE_TEMPERATURE,
        )

        if not content or not content.strip():
            raise RuntimeError("教师作业评分 LLM 返回空内容")

        self._record_message(content, MessageType.HOMEWORK_FEEDBACK)
        return content

    def _build_end_feedback_context(self) -> str:
        """构建最终总结的轻量级上下文.

        使用累积的检查点摘要 + 教师记忆，而非原始消息历史。
        注意：此方法故意不包含教学模式指令（_MODE_INSTRUCTIONS），
        因为最终总结不需要区分灌输式/启发式/讨论式。
        """
        topic = self.session_memory.topic
        teacher_context = self.memory_manager.teacher_memory.get_system_prompt_addition(topic=topic)
        full_context = self.session_memory.get_full_context()

        return f"""你是教师，正在对本次课程进行最终总结。

## 基本信息
- 教学主题: {topic}

{teacher_context}

{full_context}
"""

    def end_feedback(self) -> str:
        """生成课程结束总结和反馈.

        Returns:
            课程总结反馈内容

        Raises:
            RuntimeError: LLM 调用失败或返回空内容时
        """
        system_prompt = self._build_end_feedback_context()

        user_prompt = (
            f"课程即将结束，请对本次教学进行总结。\n\n"
            f"教学主题: {self.session_memory.topic}\n"
            f"请包含:\n"
            f"1. 本次课程的核心知识点回顾\n"
            f"2. 对学生学习情况的评价\n"
            f"3. 课后学习建议"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = safe_llm_call(
            self.llm.invoke,
            "教师",
            "课程总结",
            messages,
            temperature=DEFAULT_TEACHING_TEMPERATURE,
        )

        if not content or not content.strip():
            raise RuntimeError("教师课程总结 LLM 返回空内容")

        self._record_message(content, MessageType.END_FEEDBACK)
        return content

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

        response = safe_llm_call(
            self.llm.invoke,
            "教师",
            "内容完成度判断",
            prompt,
            temperature=CONTENT_JUDGE_TEMPERATURE,
        )

        stripped = response.strip().rstrip("。！？")
        return stripped == "完成"
