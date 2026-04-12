"""观察模式 router 异步启动单元测试."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.connection_manager import ConnectionManager, set_connection_manager
from core.session_registry import SessionRegistry, set_session_registry
from models.checkpoint.schemas import Checkpoint, CheckpointPlan


@pytest.fixture
def registry():
    """每次测试使用新的 SessionRegistry."""
    reg = SessionRegistry()
    set_session_registry(reg)
    return reg


@pytest.fixture
def cm():
    """每次测试使用新的 ConnectionManager."""
    mgr = ConnectionManager()
    set_connection_manager(mgr)
    return mgr


def _make_checkpoint_plan():
    """创建测试用 CheckpointPlan."""
    return CheckpointPlan(
        topic="Python 变量",
        teaching_mode="didactic",
        checkpoints=[
            Checkpoint(
                title="变量概念",
                key_point="变量的定义和赋值",
                checkpoint_question="什么是变量？",
            )
        ],
    )


class TestRunOrchestratorBackground:
    """_run_orchestrator_background 后台任务测试."""

    @pytest.mark.asyncio
    async def test_broadcasts_session_state_initializing(self, registry, cm):
        """后台任务启动时广播 session_state: initializing 事件."""
        mock_llm = MagicMock()
        mock_plan = _make_checkpoint_plan()

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run_autonomous_session = AsyncMock()
        mock_orchestrator_instance.stop = AsyncMock()

        cm.broadcast = AsyncMock()

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch("models.observation.service._create_memory_manager"),
            patch("models.observation.service._create_teacher_agent"),
            patch("models.observation.service._create_student_agents", return_value=[]),
            patch(
                "models.observation.service._generate_checkpoint_plan", return_value=mock_plan
            ),
            patch(
                "models.observation.service.SessionOrchestrator",
                return_value=mock_orchestrator_instance,
            ),
            patch("models.observation.service.CheckpointPlanPersistence") as mock_persistence_cls,
        ):
            mock_persistence_instance = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence_instance

            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        # 验证广播了 initializing 事件
        initializing_calls = [
            call
            for call in cm.broadcast.call_args_list
            if call[0][1].get("status") == "initializing"
        ]
        assert len(initializing_calls) == 1
        assert initializing_calls[0][0][1]["type"] == "session_state"

    @pytest.mark.asyncio
    async def test_broadcasts_session_state_running_after_init(self, registry, cm):
        """初始化完成后广播 session_state: running 事件."""
        mock_llm = MagicMock()
        mock_plan = _make_checkpoint_plan()

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run_autonomous_session = AsyncMock()
        mock_orchestrator_instance.stop = AsyncMock()

        cm.broadcast = AsyncMock()

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch("models.observation.service._create_memory_manager"),
            patch("models.observation.service._create_teacher_agent"),
            patch("models.observation.service._create_student_agents", return_value=[]),
            patch("models.observation.service._generate_checkpoint_plan", return_value=mock_plan),
            patch(
                "models.observation.service.SessionOrchestrator",
                return_value=mock_orchestrator_instance,
            ),
            patch("models.observation.service.CheckpointPlanPersistence") as mock_persistence_cls,
        ):
            mock_persistence_instance = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence_instance

            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        # 验证广播了 running 事件
        running_calls = [
            call for call in cm.broadcast.call_args_list if call[0][1].get("status") == "running"
        ]
        assert len(running_calls) == 1

    @pytest.mark.asyncio
    async def test_registers_orchestrator_after_init(self, registry, cm):
        """初始化完成后通过 register_orchestrator 注册到 registry."""
        mock_llm = MagicMock()
        mock_plan = _make_checkpoint_plan()

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run_autonomous_session = AsyncMock()
        mock_orchestrator_instance.stop = AsyncMock()

        cm.broadcast = AsyncMock()

        # 捕获 register_orchestrator 调用
        original_register = registry.register_orchestrator
        registered_orchestrators = []

        def capture_register(session_id, orchestrator):
            registered_orchestrators.append((session_id, orchestrator))
            original_register(session_id, orchestrator)

        registry.register_orchestrator = capture_register

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch("models.observation.service._create_memory_manager"),
            patch("models.observation.service._create_teacher_agent"),
            patch("models.observation.service._create_student_agents", return_value=[]),
            patch("models.observation.service._generate_checkpoint_plan", return_value=mock_plan),
            patch(
                "models.observation.service.SessionOrchestrator",
                return_value=mock_orchestrator_instance,
            ),
            patch("models.observation.service.CheckpointPlanPersistence") as mock_persistence_cls,
        ):
            mock_persistence_instance = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence_instance

            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        # 验证 register_orchestrator 被调用
        assert any(
            sid == 42 and orch is mock_orchestrator_instance
            for sid, orch in registered_orchestrators
        )

    @pytest.mark.asyncio
    async def test_runs_orchestrator_after_init(self, registry, cm):
        """初始化完成后调用 orchestrator.run_autonomous_session."""
        mock_llm = MagicMock()
        mock_plan = _make_checkpoint_plan()

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run_autonomous_session = AsyncMock()
        mock_orchestrator_instance.stop = AsyncMock()

        cm.broadcast = AsyncMock()

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch("models.observation.service._create_memory_manager"),
            patch("models.observation.service._create_teacher_agent"),
            patch("models.observation.service._create_student_agents", return_value=[]),
            patch("models.observation.service._generate_checkpoint_plan", return_value=mock_plan),
            patch(
                "models.observation.service.SessionOrchestrator",
                return_value=mock_orchestrator_instance,
            ),
            patch("models.observation.service.CheckpointPlanPersistence") as mock_persistence_cls,
        ):
            mock_persistence_instance = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence_instance

            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        mock_orchestrator_instance.run_autonomous_session.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unregisters_on_completion(self, registry, cm):
        """orchestrator 运行完成后注销 session."""
        mock_llm = MagicMock()
        mock_plan = _make_checkpoint_plan()

        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run_autonomous_session = AsyncMock()
        mock_orchestrator_instance.stop = AsyncMock()

        cm.broadcast = AsyncMock()

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch("models.observation.service._create_memory_manager"),
            patch("models.observation.service._create_teacher_agent"),
            patch("models.observation.service._create_student_agents", return_value=[]),
            patch("models.observation.service._generate_checkpoint_plan", return_value=mock_plan),
            patch(
                "models.observation.service.SessionOrchestrator",
                return_value=mock_orchestrator_instance,
            ),
            patch("models.observation.service.CheckpointPlanPersistence") as mock_persistence_cls,
        ):
            mock_persistence_instance = AsyncMock()
            mock_persistence_cls.return_value = mock_persistence_instance

            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        # orchestrator 完成后应被注销
        assert registry.get_session_info(42) is None

    @pytest.mark.asyncio
    async def test_broadcasts_error_on_failure(self, registry, cm):
        """初始化失败时广播 session_state: error 事件."""
        mock_llm = MagicMock()

        cm.broadcast = AsyncMock()

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch(
                "models.observation.service._create_memory_manager",
                side_effect=RuntimeError("内存不足"),
            ),
        ):
            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        # 验证广播了 error 事件
        error_calls = [
            call for call in cm.broadcast.call_args_list if call[0][1].get("status") == "error"
        ]
        assert len(error_calls) == 1
        assert error_calls[0][0][1].get("message", "") == "Session initialization failed"

    @pytest.mark.asyncio
    async def test_unregisters_on_error(self, registry, cm):
        """初始化失败时仍然注销 session."""
        mock_llm = MagicMock()

        cm.broadcast = AsyncMock()

        with (
            patch("models.observation.service._create_llm_client", return_value=mock_llm),
            patch(
                "models.observation.service._create_memory_manager",
                side_effect=RuntimeError("fail"),
            ),
        ):
            from models.observation.service import _run_background_task

            registry.register(session_id=42, mode="observation")
            await _run_background_task(
                session_id=42,
                topic="Python 变量",
                teaching_mode="didactic",
                students_config=[],
            )

        assert registry.get_session_info(42) is None
