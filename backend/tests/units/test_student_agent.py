"""StudentAgent 单元测试."""

import random
from unittest.mock import MagicMock

from schemas.student import StudentProfile


class TestStudentAgentInit:
    """StudentAgent 初始化测试."""

    def test_init_with_required_params(self):
        """测试使用必需参数初始化."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="张三", learning_ability=7)
        mock_llm = MagicMock()

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

        assert agent.profile is profile
        assert agent.profile.name == "张三"
        assert agent.session_memory is session_mem
        assert agent.llm is mock_llm

    def test_init_creates_memory_from_profile(self):
        """测试从 StudentProfile 创建 StudentAgentMemory."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(
            name="李四",
            level="excellent",
            attitude="active",
            learning_ability=9,
        )
        mock_llm = MagicMock()

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
        )

        assert agent.memory.name == "李四"
        assert agent.memory.level.value == "excellent"
        assert agent.memory.attitude.value == "active"
        assert agent.memory.learning_ability == 9

    def test_init_with_existing_memory(self):
        """测试使用已有的 StudentAgentMemory 初始化."""
        from agents.memories import SessionMemory
        from agents.memories.student_memory import StudentAgentMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="王五", learning_ability=5)
        mock_llm = MagicMock()

        existing_memory = StudentAgentMemory(
            name="王五",
            learned_concepts=["变量"],
            current_knowledge_level=0.3,
        )

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
            memory=existing_memory,
        )

        assert "变量" in agent.memory.learned_concepts
        assert agent.memory.current_knowledge_level == 0.3

    def test_init_with_rng(self):
        """测试使用自定义 rng 初始化."""
        from agents.memories import SessionMemory
        from agents.student_agent import StudentAgent

        session_mem = SessionMemory(session_id=1, topic="Python基础")
        profile = StudentProfile(name="赵六", learning_ability=5)
        mock_llm = MagicMock()
        test_rng = random.Random(42)

        agent = StudentAgent(
            session_memory=session_mem,
            llm=mock_llm,
            profile=profile,
            rng=test_rng,
        )

        assert agent.rng is test_rng
