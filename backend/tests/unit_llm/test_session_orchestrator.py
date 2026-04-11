"""SessionOrchestrator 单元测试."""

import pytest

from agents.memories.memory_manager import MemoryManager
from agents.memories.session_memory import SessionMemory
from agents.memories.student_memory import StudentAgentMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from agents.student_agent import StudentAgent
from agents.teacher_agent import TeacherAgent
from models.checkpoint.schemas import Checkpoint, CheckpointPlan
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
        student_profile = StudentProfile(
            name="Alice", level=StudentLevel.EXCELLENT, learning_ability=8
        )
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
            ],
        )

        # 创建 memory manager
        memory_manager = MemoryManager(
            session_memory=SessionMemory(session_id=1, topic="Test Topic"),
            teacher_memory=TeacherAgentMemory(),
            student_memories={"Alice": student_memory},
        )

        # 创建 orchestrator
        from models.session.services.observation_service import SessionOrchestrator

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager,
        )

        assert orchestrator.teacher_agent == teacher
        assert orchestrator.student_agents == [student]
        assert orchestrator.checkpoint_plan == plan
        assert orchestrator.memory_manager == memory_manager


class TestRunAutonomousSession:
    """Test run_autonomous_session method."""

    @pytest.mark.asyncio
    async def test_run_autonomous_session_basic(self):
        """测试 run_autonomous_session 基本流程."""
        from unittest.mock import AsyncMock, Mock, patch

        from agents.memories import SessionMemory
        from agents.memories.memory_manager import MemoryManager
        from agents.student_agent import StudentAgent
        from agents.teacher_agent import TeacherAgent
        from models.checkpoint.schemas import Checkpoint, CheckpointPlan
        from models.session.services.observation_service import SessionOrchestrator
        from schemas.student import StudentAttitude, StudentLevel, StudentProfile

        # Mock LLM
        mock_llm = Mock()
        mock_llm.ainvoke = AsyncMock(return_value="Test content")

        session_memory = SessionMemory(session_id=1, topic="Test Topic")
        memory_manager = MemoryManager(session_memory=session_memory)

        teacher = TeacherAgent(
            session_memory=session_memory,
            llm=mock_llm,
            teaching_mode="didactic",
        )

        student_profile = StudentProfile(
            name="Student1",
            level=StudentLevel.AVERAGE,
            attitude=StudentAttitude.NEUTRAL,
            learning_ability=5,
        )

        student = StudentAgent(
            session_memory=session_memory,
            llm=mock_llm,
            profile=student_profile,
        )

        # 创建包含 2 个检查点的计划
        plan = CheckpointPlan(
            topic="Test",
            teaching_mode="didactic",
            checkpoints=[
                Checkpoint(title="CP1", key_point="Point 1", checkpoint_question="Q1?"),
                Checkpoint(title="CP2", key_point="Point 2", checkpoint_question="Q2?"),
            ],
        )

        orchestrator = SessionOrchestrator(
            teacher_agent=teacher,
            student_agents=[student],
            checkpoint_plan=plan,
            memory_manager=memory_manager,
        )

        # Mock _teach_checkpoint 方法
        with patch.object(
            orchestrator, "_teach_checkpoint", new_callable=AsyncMock
        ) as mock_teach, patch.object(
            orchestrator, "_assign_homework", new_callable=AsyncMock
        ) as mock_hw, patch.object(
            orchestrator, "_collect_homework_and_feedback", new_callable=AsyncMock
        ):
            await orchestrator.run_autonomous_session()

            # 验证调用了 2 次 _teach_checkpoint (每个检查点一次)
            assert mock_teach.call_count == 2

            # 验证最后一次调用了 _assign_homework
            mock_hw.assert_called_once()
