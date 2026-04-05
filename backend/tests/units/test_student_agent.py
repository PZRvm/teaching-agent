"""StudentAgent 单元测试."""

import random
from unittest.mock import MagicMock

from agents.memories import SessionMemory
from agents.student_agent import StudentAgent
from schemas.student import StudentProfile


def _make_agent(
    *,
    name: str = "测试学生",
    level: str = "average",
    attitude: str = "neutral",
    learning_ability: int = 5,
    mock_return: str = "",
    rng_seed: int | None = None,
    memory=None,
):
    """创建 StudentAgent 测试实例的通用工厂函数."""
    session_mem = SessionMemory(session_id=1, topic="Python基础")
    profile = StudentProfile(
        name=name,
        level=level,
        attitude=attitude,
        learning_ability=learning_ability,
    )
    mock_llm = MagicMock()
    if mock_return:
        mock_llm.invoke.return_value = mock_return

    kwargs: dict = {
        "session_memory": session_mem,
        "llm": mock_llm,
        "profile": profile,
    }
    if rng_seed is not None:
        kwargs["rng"] = random.Random(rng_seed)
    if memory is not None:
        kwargs["memory"] = memory

    return StudentAgent(**kwargs)


class TestStudentAgentInit:
    """StudentAgent 初始化测试."""

    def test_init_with_required_params(self):
        """测试使用必需参数初始化."""
        agent = _make_agent(name="张三", learning_ability=7)

        assert agent.profile.name == "张三"
        assert agent.session_memory is not None
        assert agent.llm is not None

    def test_init_creates_memory_from_profile(self):
        """测试从 StudentProfile 创建 StudentAgentMemory."""
        agent = _make_agent(
            name="李四",
            level="excellent",
            attitude="active",
            learning_ability=9,
        )

        assert agent.memory.name == "李四"
        assert agent.memory.level.value == "excellent"
        assert agent.memory.attitude.value == "active"
        assert agent.memory.learning_ability == 9

    def test_init_with_existing_memory(self):
        """测试使用已有的 StudentAgentMemory 初始化."""
        from agents.memories.student_memory import StudentAgentMemory

        existing_memory = StudentAgentMemory(
            name="王五",
            learned_concepts=["变量"],
            current_knowledge_level=0.3,
        )

        agent = _make_agent(name="王五", memory=existing_memory)

        assert "变量" in agent.memory.learned_concepts
        assert agent.memory.current_knowledge_level == 0.3

    def test_init_with_rng(self):
        """测试使用自定义 rng 初始化."""
        test_rng = random.Random(42)

        agent = _make_agent(rng_seed=None)
        agent.rng = test_rng

        assert agent.rng is test_rng


class TestStudentAgentShouldRespond:
    """StudentAgent should_respond 测试."""

    def test_active_student_responds_most_of_the_time(self):
        """测试积极学生大概率响应."""
        agent = _make_agent(attitude="active", rng_seed=42)

        results = [agent.should_respond() for _ in range(100)]
        respond_rate = sum(results) / len(results)

        assert respond_rate > 0.6

    def test_neutral_student_responds_half_the_time(self):
        """测试中性学生约 50% 响应."""
        agent = _make_agent(attitude="neutral", rng_seed=42)

        results = [agent.should_respond() for _ in range(100)]
        respond_rate = sum(results) / len(results)

        assert 0.3 < respond_rate < 0.7

    def test_passive_student_responds_less(self):
        """测试消极学生响应较少."""
        agent = _make_agent(attitude="passive", rng_seed=42)

        results = [agent.should_respond() for _ in range(100)]
        respond_rate = sum(results) / len(results)

        assert respond_rate < 0.4

    def test_should_respond_returns_boolean(self):
        """测试 should_respond 返回布尔值."""
        agent = _make_agent()

        result = agent.should_respond()

        assert isinstance(result, bool)


class TestStudentAgentAnswerQuestion:
    """StudentAgent answer_question 测试."""

    def _make_agent(self, *, level: str = "average", attitude: str = "neutral"):
        return _make_agent(
            name="张三",
            level=level,
            attitude=attitude,
            learning_ability=6,
            mock_return="Python中的变量用来存储数据，可以用等号赋值。",
        )

    def test_answer_question_calls_llm(self):
        """测试 answer_question 调用 LLM."""
        agent = self._make_agent()

        agent.answer_question("什么是Python变量？")

        assert agent.llm.invoke.called

    def test_answer_question_includes_question_in_prompt(self):
        """测试 answer_question 在 prompt 中包含教师问题."""
        agent = self._make_agent()

        agent.answer_question("什么是Python变量？")

        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[-1]["content"]
        assert "Python" in user_msg

    def test_answer_question_includes_student_context(self):
        """测试 answer_question 的 system prompt 包含学生上下文."""
        agent = self._make_agent()

        agent.answer_question("如何定义一个Python函数？")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "张三" in system_msg
        assert "Python基础" in system_msg

    def test_answer_question_excellent_student_has_higher_quality_prompt(self):
        """测试优秀学生的 prompt 包含更高质量要求."""
        agent = self._make_agent(level="excellent")

        agent.answer_question("如何定义一个Python函数？")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "举一反三" in system_msg

    def test_answer_question_basic_student_has_basic_prompt(self):
        """测试基础学生的 prompt 包含基础水平描述."""
        agent = self._make_agent(level="basic")

        agent.answer_question("如何定义一个Python函数？")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "混淆概念" in system_msg

    def test_answer_question_returns_llm_response(self):
        """测试 answer_question 返回 LLM 响应."""
        agent = self._make_agent()

        result = agent.answer_question("什么是Python变量？")

        assert result == "Python中的变量用来存储数据，可以用等号赋值。"

    def test_answer_question_records_message_in_session_memory(self):
        """测试 answer_question 将消息记录到会话记忆."""
        agent = self._make_agent()

        agent.answer_question("什么是Python变量？")

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "张三"
        assert msg.message_type.value == "answer_to_checkpoint"


class TestStudentAgentAskQuestion:
    """StudentAgent ask_question 测试."""

    def _make_agent(self, *, attitude: str = "neutral"):
        return _make_agent(
            name="李四",
            attitude=attitude,
            learning_ability=5,
            mock_return="老师，列表和元组有什么区别？",
        )

    def test_ask_question_calls_llm(self):
        """测试 ask_question 调用 LLM."""
        agent = self._make_agent()

        agent.ask_question("刚才讲的列表操作")

        assert agent.llm.invoke.called

    def test_ask_question_includes_teaching_context(self):
        """测试 ask_question 的 prompt 包含教学内容上下文."""
        agent = self._make_agent()

        agent.ask_question("刚才讲的列表操作")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "Python基础" in system_msg
        assert "李四" in system_msg

    def test_ask_question_returns_question_text(self):
        """测试 ask_question 返回问题文本."""
        agent = self._make_agent()

        result = agent.ask_question("列表操作")

        assert result == "老师，列表和元组有什么区别？"

    def test_ask_question_records_message(self):
        """测试 ask_question 记录消息到会话记忆."""
        agent = self._make_agent()

        agent.ask_question("列表操作")

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "李四"
        assert msg.message_type.value == "question_to_teacher"


class TestStudentAgentSubmitHomework:
    """StudentAgent submit_homework 测试."""

    def _make_agent(self, *, level: str = "average", learning_ability: int = 5):
        return _make_agent(
            name="王五",
            level=level,
            learning_ability=learning_ability,
            mock_return="def calculate_average(numbers):\n    return sum(numbers) / len(numbers)",
        )

    def test_submit_homework_calls_llm(self):
        """测试 submit_homework 调用 LLM."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        assert agent.llm.invoke.called

    def test_submit_homework_includes_homework_prompt(self):
        """测试 submit_homework 的 prompt 包含作业要求."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[-1]["content"]

        assert "平均" in user_msg

    def test_submit_homework_includes_student_context(self):
        """测试 submit_homework 的 system prompt 包含学生上下文."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "王五" in system_msg

    def test_submit_homework_returns_response(self):
        """测试 submit_homework 返回 LLM 响应."""
        agent = self._make_agent()

        result = agent.submit_homework("写一个函数计算列表的平均值")

        assert "def" in result

    def test_submit_homework_records_message(self):
        """测试 submit_homework 记录消息."""
        agent = self._make_agent()

        agent.submit_homework("写一个函数计算列表的平均值")

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "王五"
        assert msg.message_type.value == "homework_submission"


class TestStudentAgentGiveFeedback:
    """StudentAgent give_feedback 测试."""

    def _make_agent(self, *, attitude: str = "neutral"):
        return _make_agent(
            name="赵六",
            attitude=attitude,
            learning_ability=6,
            mock_return="今天的课我学到了列表操作，但对列表推导式还不太理解。",
        )

    def test_give_feedback_calls_llm(self):
        """测试 give_feedback 调用 LLM."""
        agent = self._make_agent()

        agent.give_feedback()

        assert agent.llm.invoke.called

    def test_give_feedback_includes_feedback_prompt(self):
        """测试 give_feedback 的 prompt 包含反馈请求."""
        agent = self._make_agent()

        agent.give_feedback()

        messages = agent.llm.invoke.call_args[0][0]
        user_msg = messages[-1]["content"]

        assert "反馈" in user_msg or "总结" in user_msg

    def test_give_feedback_includes_student_context(self):
        """测试 give_feedback 的 system prompt 包含学生上下文."""
        agent = self._make_agent()

        agent.give_feedback()

        messages = agent.llm.invoke.call_args[0][0]
        system_msg = messages[0]["content"]

        assert "赵六" in system_msg
        assert "Python基础" in system_msg

    def test_give_feedback_returns_response(self):
        """测试 give_feedback 返回反馈文本."""
        agent = self._make_agent()

        result = agent.give_feedback()

        assert "列表操作" in result

    def test_give_feedback_records_message(self):
        """测试 give_feedback 记录消息."""
        agent = self._make_agent()

        agent.give_feedback()

        assert len(agent.session_memory.message_history) == 1
        msg = agent.session_memory.message_history[0]
        assert msg.sender == "赵六"
        assert msg.message_type.value == "feedback_submission"


class TestStudentAgentEmptyContent:
    """StudentAgent 空内容处理测试."""

    def _make_agent(self):
        return _make_agent(
            name="测试生",
            mock_return="正常回答",
        )

    def test_empty_llm_response_does_not_record_message(self):
        """测试 LLM 返回空字符串时不记录消息."""
        from unittest.mock import patch

        agent = self._make_agent()

        with patch("agents.student_agent.safe_llm_call", return_value=""):
            result = agent.answer_question("测试问题？")

        assert result == ""
        assert len(agent.session_memory.message_history) == 0

    def test_whitespace_llm_response_does_not_record_message(self):
        """测试 LLM 返回纯空白时不记录消息."""
        from unittest.mock import patch

        agent = self._make_agent()

        with patch("agents.student_agent.safe_llm_call", return_value="   \n\t  "):
            result = agent.answer_question("测试问题？")

        assert result == ""
        assert len(agent.session_memory.message_history) == 0

    def test_normal_response_records_message(self):
        """测试正常响应正确记录消息."""
        from unittest.mock import patch

        agent = self._make_agent()

        with patch("agents.student_agent.safe_llm_call", return_value="正常回答"):
            result = agent.answer_question("测试问题？")

        assert result == "正常回答"
        assert len(agent.session_memory.message_history) == 1
