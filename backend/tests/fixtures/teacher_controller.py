"""TeacherSessionController 测试 fixtures."""

import pytest

from agents.memories.memory_manager import MemoryManager
from agents.memories.session_memory import SessionMemory
from agents.memories.teacher_memory import TeacherAgentMemory
from agents.student_agent import StudentAgent
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from models.session.services.teacher_service import TeacherSessionController
from schemas.student import StudentAttitude, StudentLevel


@pytest.fixture
def sample_checkpoint_plan():
    """创建测试用检查点计划."""
    return CheckpointPlan(
        topic="Python 变量与数据类型",
        teaching_mode="teacher",
        checkpoints=[
            Checkpoint(
                title="Python 变量的定义与赋值",
                key_point="Python 是动态类型语言，变量无需声明类型，使用 = 赋值",
                checkpoint_question="Python 中的变量和数学中的变量有什么区别？",
                state=CheckpointState.PENDING,
            ),
            Checkpoint(
                title="Python 基本数据类型",
                key_point="Python 有 int、float、str、bool 等基本数据类型，可用 type() 查看类型",
                checkpoint_question="如何判断一个变量的类型？",
                state=CheckpointState.PENDING,
            ),
            Checkpoint(
                title="Python 容器类型：列表和字典",
                key_point="列表是有序的可变序列，字典是无序的键值对集合",
                checkpoint_question="列表和字典的主要区别是什么？",
                state=CheckpointState.PENDING,
            ),
        ],
        current_index=0,
    )


@pytest.fixture
def sample_student_agents(sample_memory_manager):
    """创建测试用学生 agents."""
    students = []
    for i, (level, attitude) in enumerate(
        [
            (StudentLevel.EXCELLENT, StudentAttitude.ACTIVE),
            (StudentLevel.AVERAGE, StudentAttitude.NEUTRAL),
        ],
        start=1,
    ):
        from schemas.student import StudentProfile

        profile = StudentProfile(
            name=f"Student{i}",
            level=level,
            attitude=attitude,
            learning_ability=7,
        )
        # 使用 mock LLM
        from unittest.mock import Mock

        mock_llm = Mock()
        mock_llm.invoke = Mock(return_value="Mock response")
        students.append(
            StudentAgent(
                session_memory=sample_memory_manager.session_memory, profile=profile, llm=mock_llm
            )
        )
    return students


@pytest.fixture
def sample_memory_manager():
    """创建测试用记忆管理器."""
    session_memory = SessionMemory(session_id=1, topic="Python 变量与数据类型")
    teacher_memory = TeacherAgentMemory()
    return MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)


@pytest.fixture
def teacher_controller(sample_checkpoint_plan, sample_student_agents, sample_memory_manager):
    """创建 TeacherSessionController 实例."""
    return TeacherSessionController(
        student_agents=sample_student_agents,
        memory_manager=sample_memory_manager,
        checkpoint_plan=sample_checkpoint_plan,
        ws_push_callback=None,
    )


def create_test_controller():
    """便捷函数：创建测试用控制器（用于单元测试）.

    Returns:
        TeacherSessionController 实例，包含模拟数据
    """
    from unittest.mock import Mock

    from schemas.student import StudentProfile

    # 创建测试用检查点计划
    plan = CheckpointPlan(
        topic="Python 变量与数据类型",
        teaching_mode="teacher",
        checkpoints=[
            Checkpoint(
                title="Python 变量的定义与赋值",
                key_point="Python 是动态类型语言，变量无需声明类型",
                checkpoint_question="Python 中的变量和数学中的变量有什么区别？",
                state=CheckpointState.PENDING,
            ),
        ],
        current_index=0,
    )

    # 创建记忆管理器
    session_memory = SessionMemory(session_id=1, topic="Python 变量与数据类型")
    teacher_memory = TeacherAgentMemory()
    memory_manager = MemoryManager(session_memory=session_memory, teacher_memory=teacher_memory)

    # 创建测试用学生
    profile = StudentProfile(
        name="测试学生",
        level=StudentLevel.AVERAGE,
        attitude=StudentAttitude.ACTIVE,
        learning_ability=7,
    )
    mock_llm = Mock()
    mock_llm.invoke = Mock(return_value="Mock response")

    # 创建控制器
    return TeacherSessionController(
        student_agents=[StudentAgent(session_memory=session_memory, profile=profile, llm=mock_llm)],
        memory_manager=memory_manager,
        checkpoint_plan=plan,
        ws_push_callback=None,
    )
