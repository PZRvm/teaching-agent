"""TeacherAgent 单元测试."""

from unittest.mock import MagicMock

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
