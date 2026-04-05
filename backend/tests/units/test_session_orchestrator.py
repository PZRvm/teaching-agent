"""SessionOrchestrator 单元测试."""

import pytest
from agents.memories.memory_manager import MemoryManager
from agents.memories.session_memory import SessionMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from agents.memories.student_memory import StudentAgentMemory
from agents.student_agent import StudentAgent
from agents.teacher_agent import TeacherAgent
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from schemas.student import StudentLevel, StudentProfile


class TestSessionOrchestratorInit:
    """Test SessionOrchestrator initialization."""

    def test_orchestrator_init(self):
        """Test creating SessionOrchestrator with required parameters."""
        # 创建 mock teacher agent
        teacher = TeacherAgent(
            session_memory=SessionMemory(session_id=1, topic="Test Topic"),
            llm=None,  # Mock for initialization test
        )

        # 创建 mock student agent
        student_profile = StudentProfile(name="Alice", level=StudentLevel.EXCELLENT, learning_ability=8)
        student_memory = StudentAgentMemory.from_profile(student_profile)
        student = StudentAgent(
            session_memory=SessionMemory(session_id=1, topic="Test Topic"),
            profile=student_profile,
            memory=student_memory,
            llm=None,  # Mock for initialization test
        )

        # 创建 checkpoint plan
        plan = CheckpointPlan(
            topic="Python Basics",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(
                    title="Introduction to Python",
                    key_point="Python is a high-level programming language",
                    checkpoint_question="What is Python?",
                )
            ]
        )

        # 创建 memory manager
        memory_manager = MemoryManager(
            session_memory=SessionMemory(session_id=1, topic="Test Topic"),
            teacher_memory=TeacherAgentMemory(),
            student_memories={"Alice": student_memory},
        )

        # 创建 orchestrator
        from models.session.orchestrator import SessionOrchestrator

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager
        )

        assert orchestrator.teacher_agent == teacher
        assert orchestrator.student_agents == [student]
        assert orchestrator.checkpoint_plan == plan
        assert orchestrator.memory_manager == memory_manager
