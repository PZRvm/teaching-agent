"""TeacherAgent 单元测试."""

from unittest.mock import MagicMock

from schemas.message import MessageType
from schemas.student import StudentProfile


class TestTeacherAgentInit:
    """TeacherAgent 初始化测试."""

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
