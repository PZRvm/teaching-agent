"""TeacherSessionController 单元测试."""

import pytest
from unittest.mock import Mock

from models.session.teacher_controller import TeacherSessionController
from models.checkpoint.schemas import Checkpoint, CheckpointPlan, CheckpointState
from agents.memories import SessionMemory, TeacherAgentMemory
from agents.student_agent import StudentAgent
from schemas.student import StudentLevel, StudentAttitude, StudentProfile


class TestTeacherSessionControllerInit:
    """TeacherSessionController 初始化测试"""

    def test_init_creates_controller_with_required_components(self):
        """测试初始化创建控制器及其必需组件"""
        # Arrange
        mock_student_agents = [Mock(), Mock()]
        mock_memory_manager = Mock()
        mock_checkpoint_plan = Mock()
        mock_ws_callback = Mock()

        # Act
        controller = TeacherSessionController(
            student_agents=mock_student_agents,
            memory_manager=mock_memory_manager,
            checkpoint_plan=mock_checkpoint_plan,
            ws_push_callback=mock_ws_callback
        )

        # Assert
        assert controller.student_agents == mock_student_agents
        assert controller.memory_manager == mock_memory_manager
        assert controller.checkpoint_plan == mock_checkpoint_plan
        assert controller._ws_push_callback == mock_ws_callback
        assert controller._active_dialogue is None  # 初始无活跃对话
        assert controller._dialogue_round_count == 0
