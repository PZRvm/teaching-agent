"""TeacherAgent 单元测试."""

from unittest.mock import MagicMock

from schemas.message import MessageType
from schemas.student import StudentProfile


class TestTeacherAgentInit:
    """TeacherAgent 初始化测试."""

    def test_invalid_teaching_mode_raises_error(self):
        """测试无效教学模式抛出 ValueError."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        import pytest

        with pytest.raises(ValueError, match="无效的教学模式"):
            TeacherAgent(
                session_memory=session_mem,
                llm=mock_llm,
                teaching_mode="invalid_mode",
            )

    def test_init_with_defaults(self):
        """测试使用 MemoryManager 初始化."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
        )

        assert agent.session_memory is session_mem
        assert agent.teaching_mode == "didactic"
        assert agent.llm is mock_llm

    def test_init_default_teaching_mode(self):
        """测试默认教学模式为 didactic."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
        )

        assert agent.teaching_mode == "didactic"

    def test_init_registers_students(self):
        """测试初始化时注册学生到 MemoryManager."""
        from agents.memories import SessionMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        mock_llm = MagicMock()

        profiles = [
            StudentProfile(name="张三", learning_ability=8),
            StudentProfile(name="李四", learning_ability=5),
        ]

        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            students=profiles,
        )

        assert "张三" in agent.memory_manager.student_memories
        assert "李四" in agent.memory_manager.student_memories

    def test_init_with_existing_memory_manager(self):
        """测试使用已有的 MemoryManager 初始化."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        teacher_mem.record_covered_topic("已有知识点")

        from agents.memories.memory_manager import MemoryManager

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)

        mock_llm = MagicMock()
        agent = TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            memory_manager=mm,
        )

        assert "已有知识点" in agent.memory_manager.teacher_memory.covered_topics


class TestTeacherAgentLecture:
    """TeacherAgent 讲授功能测试."""

    def _make_agent(
        self, teaching_mode: str = "didactic", covered_topics: list[str] | None = None
    ):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "这是关于变量的讲授内容。"

        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_deliver_lecture_calls_llm(self):
        """测试 deliver_lecture 调用 LLM."""
        agent = self._make_agent()

        agent.deliver_lecture()

        assert len(agent.llm.invoke.call_args_list) == 1

    def test_deliver_lecture_passes_system_prompt_with_context(self):
        """测试 deliver_lecture 传递包含记忆上下文的 system prompt."""
        agent = self._make_agent(covered_topics=["变量"])

        agent.deliver_lecture()

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "Python基础" in system_msg
        assert "变量" in system_msg  # 已讲授内容
        assert "灌输式" in system_msg  # 教学模式

    def test_deliver_lecture_uses_mode_temperature(self):
        """测试不同教学模式使用不同温度."""
        # 灌输式 = 0.3
        agent_didactic = self._make_agent(teaching_mode="didactic")
        agent_didactic.deliver_lecture()
        assert agent_didactic.llm.invoke.call_args[1].get("temperature") == 0.3

        # 启发式 = 0.5
        agent_heuristic = self._make_agent(teaching_mode="heuristic")
        agent_heuristic.deliver_lecture()
        assert agent_heuristic.llm.invoke.call_args[1].get("temperature") == 0.5

        # 讨论式 = 0.7
        agent_discussion = self._make_agent(teaching_mode="discussion")
        agent_discussion.deliver_lecture()
        assert agent_discussion.llm.invoke.call_args[1].get("temperature") == 0.7

    def test_deliver_lecture_updates_memory_manager(self):
        """测试 deliver_lecture 通过 MemoryManager 更新记忆."""
        agent = self._make_agent()

        # Mock LLM 返回包含知识点的内容
        agent.llm.invoke.return_value = "今天我们学习变量和数据类型。"

        # Mock extract_knowledge_fn
        agent.memory_manager.extract_knowledge_fn = lambda c: ["变量", "数据类型"]

        agent.deliver_lecture()

        assert "变量" in agent.memory_manager.teacher_memory.covered_topics
        assert "数据类型" in agent.memory_manager.teacher_memory.covered_topics
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.LECTURE

    def test_deliver_lecture_heuristic_mode_includes_interaction(self):
        """测试启发式模式的 system prompt 包含互动指令."""
        agent = self._make_agent(teaching_mode="heuristic")

        agent.deliver_lecture()

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "checkpoint" in system_msg.lower() or "提问" in system_msg.lower()

    def test_deliver_lecture_discussion_mode_includes_discussion(self):
        """测试讨论式模式的 system prompt 包含讨论指令."""
        agent = self._make_agent(teaching_mode="discussion")

        agent.deliver_lecture()

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "讨论" in system_msg.lower()


class TestTeacherAgentContentComplete:
    """TeacherAgent 内容完成判断测试."""

    def _make_agent(self, covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础变量")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "未完成"

        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            memory_manager=mm,
        )

    def test_content_complete_no_topics_returns_false(self):
        """测试无已讲授知识点时返回 False."""
        agent = self._make_agent()

        assert agent.is_content_complete() is False

    def test_content_complete_with_partial_topics(self):
        """测试部分知识点时返回 False."""
        agent = self._make_agent(covered_topics=["变量"])

        assert agent.is_content_complete() is False

    def test_content_complete_with_all_topics_returns_true(self):
        """测试知识点完整覆盖时返回 True."""
        agent = self._make_agent(covered_topics=["变量", "数据类型", "条件语句", "循环"])

        agent.llm.invoke.return_value = "完成"

        assert agent.is_content_complete() is True

    def test_content_complete_sends_topic_and_topics(self):
        """测试 LLM 调用包含教学主题和知识点列表."""
        agent = self._make_agent(covered_topics=["变量"])

        agent.is_content_complete()

        prompt = agent.llm.invoke.call_args[0][0]

        assert "Python基础变量" in prompt
        assert "变量" in prompt

    def test_content_complete_with_trailing_punctuation(self):
        """测试 LLM 返回带标点的「完成」仍然判定为完成."""
        agent = self._make_agent(covered_topics=["变量", "数据类型", "条件语句", "循环"])

        for response in ("完成。", "完成！", "完成？"):
            agent.llm.invoke.return_value = response
            assert agent.is_content_complete() is True, f"Failed for: {response}"


class TestTeacherAgentDeliverLectureErrors:
    """TeacherAgent deliver_lecture 错误路径测试."""

    def _make_agent(self):
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_deliver_lecture_raises_runtime_error_on_llm_failure(self):
        """测试 LLM 调用失败时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.side_effect = ConnectionError("API error")

        with pytest.raises(RuntimeError, match=".*讲授.*失败"):
            agent.deliver_lecture()

    def test_deliver_lecture_no_message_recorded_on_failure(self):
        """测试 LLM 失败时不记录消息."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.side_effect = ConnectionError("API error")

        with pytest.raises(RuntimeError):
            agent.deliver_lecture()

        assert len(agent.session_memory.message_history) == 0

    def test_deliver_lecture_raises_on_empty_content(self):
        """测试 LLM 返回空内容时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = ""

        with pytest.raises(RuntimeError, match="空内容"):
            agent.deliver_lecture()

    def test_deliver_lecture_raises_on_whitespace_content(self):
        """测试 LLM 返回纯空白时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.invoke.return_value = "   \n\t  "

        with pytest.raises(RuntimeError, match="空内容"):
            agent.deliver_lecture()


class TestTeacherAgentStreamErrors:
    """TeacherAgent deliver_lecture_stream 错误路径测试."""

    def _make_agent(self):
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_stream_raises_runtime_error_on_failure(self):
        """测试 stream 失败时抛出 RuntimeError."""
        import pytest

        agent = self._make_agent()
        agent.llm.stream.side_effect = ConnectionError("stream broke")

        with pytest.raises(RuntimeError, match=".*stream.*失败"):
            list(agent.deliver_lecture_stream())

    def test_stream_empty_does_not_record(self):
        """测试空 stream 不记录讲授内容."""
        agent = self._make_agent()
        agent.llm.stream.return_value = iter([])

        list(agent.deliver_lecture_stream())

        assert len(agent.session_memory.message_history) == 0

    def test_stream_success_records_lecture(self):
        """测试成功 stream 记录完整讲授内容."""
        agent = self._make_agent()

        def fake_stream(*a, **kw):
            yield "Hello "
            yield "World"

        agent.llm.stream.return_value = fake_stream()

        chunks = list(agent.deliver_lecture_stream())

        assert chunks == ["Hello ", "World"]
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].content == "Hello World"

    def test_stream_error_does_not_record_partial(self):
        """测试 stream 中途失败不记录部分内容."""
        import pytest

        agent = self._make_agent()

        def failing_stream(*a, **kw):
            yield "chunk1"
            raise ConnectionError("mid-stream error")

        agent.llm.stream.return_value = failing_stream()

        with pytest.raises(RuntimeError):
            list(agent.deliver_lecture_stream())

        assert len(agent.session_memory.message_history) == 0


class TestTeacherAgentCheckpointQuestion:
    """TeacherAgent ask_checkpoint_question 测试."""

    def _make_agent(self, teaching_mode: str = "heuristic", covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "请问变量的作用域有哪些？"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_ask_checkpoint_question_calls_llm(self):
        """测试 ask_checkpoint_question 调用 LLM."""
        agent = self._make_agent()
        agent.ask_checkpoint_question()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_ask_checkpoint_question_prompt_includes_covered_topics(self):
        """测试 prompt 包含已讲授知识点."""
        agent = self._make_agent(covered_topics=["变量", "数据类型"])
        agent.ask_checkpoint_question()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "变量" in user_msg

    def test_ask_checkpoint_question_uses_mode_temperature(self):
        """测试使用对应模式的温度."""
        agent = self._make_agent(teaching_mode="heuristic")
        agent.ask_checkpoint_question()
        assert agent.llm.invoke.call_args[1].get("temperature") == 0.5

    def test_ask_checkpoint_question_returns_content(self):
        """测试返回 LLM 生成的问题内容."""
        agent = self._make_agent()
        result = agent.ask_checkpoint_question()
        assert result == "请问变量的作用域有哪些？"

    def test_ask_checkpoint_question_records_message(self):
        """测试记录为 CHECKPOINT_QUESTION 消息."""
        agent = self._make_agent()
        agent.ask_checkpoint_question()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.CHECKPOINT_QUESTION


class TestTeacherAgentDiscussionQuestion:
    """TeacherAgent ask_discussion_question 测试."""

    def _make_agent(self, teaching_mode: str = "discussion", covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "大家觉得在实际项目中，什么时候应该用列表，什么时候应该用元组？"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_ask_discussion_question_calls_llm(self):
        """测试 ask_discussion_question 调用 LLM."""
        agent = self._make_agent()
        agent.ask_discussion_question()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_ask_discussion_question_prompt_includes_topic(self):
        """测试 prompt 包含教学主题."""
        agent = self._make_agent()
        agent.ask_discussion_question()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "Python基础" in user_msg

    def test_ask_discussion_question_uses_mode_temperature(self):
        """测试讨论式模式使用 0.7 温度."""
        agent = self._make_agent(teaching_mode="discussion")
        agent.ask_discussion_question()
        assert agent.llm.invoke.call_args[1].get("temperature") == 0.7

    def test_ask_discussion_question_returns_content(self):
        """测试返回 LLM 生成的讨论问题."""
        agent = self._make_agent()
        result = agent.ask_discussion_question()
        assert result == "大家觉得在实际项目中，什么时候应该用列表，什么时候应该用元组？"

    def test_ask_discussion_question_records_as_checkpoint(self):
        """测试记录为 CHECKPOINT_QUESTION 消息."""
        agent = self._make_agent()
        agent.ask_discussion_question()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.CHECKPOINT_QUESTION


class TestTeacherAgentReplyToStudent:
    """TeacherAgent reply_to_student 测试."""

    def _make_agent(self, teaching_mode: str = "heuristic"):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "回答得很好！变量确实有局部和全局两种作用域。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode=teaching_mode,
            memory_manager=mm,
        )

    def test_reply_to_student_calls_llm(self):
        """测试 reply_to_student 调用 LLM."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_reply_to_student_prompt_includes_student_name(self):
        """测试 prompt 包含学生名字."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "张三" in user_msg

    def test_reply_to_student_prompt_includes_student_message(self):
        """测试 prompt 包含学生消息内容."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "变量有局部和全局作用域" in user_msg

    def test_reply_to_student_returns_content(self):
        """测试返回 LLM 生成的回复内容."""
        agent = self._make_agent()
        result = agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        assert result == "回答得很好！变量确实有局部和全局两种作用域。"

    def test_reply_to_student_records_as_teacher_reply(self):
        """测试记录为 TEACHER_REPLY 消息."""
        agent = self._make_agent()
        agent.reply_to_student(student_name="张三", student_message="变量有局部和全局作用域。")
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.TEACHER_REPLY


class TestTeacherAgentAssignHomework:
    """TeacherAgent assign_homework 测试."""

    def _make_agent(self, covered_topics: list[str] | None = None):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        if covered_topics:
            for t in covered_topics:
                teacher_mem.record_covered_topic(t)

        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "作业：请编写一个函数，实现列表的排序功能。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_assign_homework_calls_llm(self):
        """测试 assign_homework 调用 LLM."""
        agent = self._make_agent()
        agent.assign_homework()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_assign_homework_prompt_includes_topic_and_topics(self):
        """测试 prompt 包含教学主题和已讲授知识点."""
        agent = self._make_agent(covered_topics=["变量", "函数"])
        agent.assign_homework()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "Python基础" in user_msg
        assert "变量" in user_msg

    def test_assign_homework_returns_content(self):
        """测试返回作业内容."""
        agent = self._make_agent()
        result = agent.assign_homework()
        assert result == "作业：请编写一个函数，实现列表的排序功能。"

    def test_assign_homework_records_as_assign_homework(self):
        """测试记录为 ASSIGN_HOMEWORK 消息."""
        agent = self._make_agent()
        agent.assign_homework()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.ASSIGN_HOMEWORK


class TestTeacherAgentGradeHomework:
    """TeacherAgent grade_homework 测试."""

    def _make_agent(self):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "评分：良好。优点：函数逻辑正确。改进：缺少边界条件处理。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_grade_homework_calls_llm(self):
        """测试 grade_homework 调用 LLM."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_grade_homework_prompt_includes_student_name(self):
        """测试 prompt 包含学生名字."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "张三" in user_msg

    def test_grade_homework_prompt_includes_homework_content(self):
        """测试 prompt 包含作业内容."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "def sort" in user_msg

    def test_grade_homework_uses_low_temperature(self):
        """测试使用低温度进行评分（CONTENT_JUDGE_TEMPERATURE）."""
        from core.settings import CONTENT_JUDGE_TEMPERATURE

        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        assert agent.llm.invoke.call_args[1].get("temperature") == CONTENT_JUDGE_TEMPERATURE

    def test_grade_homework_records_as_homework_feedback(self):
        """测试记录为 HOMEWORK_FEEDBACK 消息."""
        agent = self._make_agent()
        agent.grade_homework(student_name="张三", homework_content="def sort(lst): return sorted(lst)")
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.HOMEWORK_FEEDBACK


class TestTeacherAgentEndFeedback:
    """TeacherAgent end_feedback 测试."""

    def _make_agent(self):
        """辅助方法：创建 TeacherAgent."""
        from agents.memories import SessionMemory, TeacherAgentMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.teacher_agent import TeacherAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        teacher_mem = TeacherAgentMemory()
        mm = MemoryManager(session_memory=session_mem, teacher_memory=teacher_mem)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "本次课程我们学习了Python基础，大家表现不错，课后多练习。"
        return TeacherAgent(
            session_memory=session_mem,
            llm=mock_llm,
            teaching_mode="didactic",
            memory_manager=mm,
        )

    def test_end_feedback_calls_llm(self):
        """测试 end_feedback 调用 LLM."""
        agent = self._make_agent()
        agent.end_feedback()
        assert len(agent.llm.invoke.call_args_list) == 1

    def test_end_feedback_prompt_includes_topic(self):
        """测试 prompt 包含教学主题."""
        agent = self._make_agent()
        agent.end_feedback()
        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[1]["content"]
        assert "Python基础" in user_msg

    def test_end_feedback_returns_content(self):
        """测试返回课程总结内容."""
        agent = self._make_agent()
        result = agent.end_feedback()
        assert result == "本次课程我们学习了Python基础，大家表现不错，课后多练习。"

    def test_end_feedback_records_as_end_feedback(self):
        """测试记录为 END_FEEDBACK 消息."""
        agent = self._make_agent()
        agent.end_feedback()
        assert len(agent.session_memory.message_history) == 1
        assert agent.session_memory.message_history[0].message_type == MessageType.END_FEEDBACK
