from unittest.mock import MagicMock

from core.session_registry import SessionRegistry


class TestSessionRegistry:
    """SessionRegistry 单元测试."""

    def test_register_and_get_orchestrator(self):
        """注册并获取 orchestrator."""
        registry = SessionRegistry()
        mock_orchestrator = MagicMock()
        registry.register(session_id=1, mode="observation", orchestrator=mock_orchestrator)

        result = registry.get_orchestrator(session_id=1)
        assert result is mock_orchestrator

    def test_register_and_get_controller(self):
        """注册并获取 teacher controller."""
        registry = SessionRegistry()
        mock_controller = MagicMock()
        registry.register(session_id=2, mode="teacher", controller=mock_controller)

        result = registry.get_controller(session_id=2)
        assert result is mock_controller

    def test_get_nonexistent_session(self):
        """获取不存在的 session 返回 None."""
        registry = SessionRegistry()
        assert registry.get_orchestrator(session_id=999) is None
        assert registry.get_controller(session_id=999) is None

    def test_unregister(self):
        """注销 session."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="observation", orchestrator=MagicMock())
        registry.unregister(session_id=1)
        assert registry.get_orchestrator(session_id=1) is None


class TestSessionRegistryTypes:
    """SessionRegistry 类型标注和 get_session_info 测试."""

    def test_get_orchestrator_none_for_teacher_session(self):
        """教师模式会话的 get_orchestrator 返回 None."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="teacher", controller=MagicMock())

        assert registry.get_orchestrator(session_id=1) is None

    def test_get_controller_none_for_observation_session(self):
        """观察模式会话的 get_controller 返回 None."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="observation", orchestrator=MagicMock())

        assert registry.get_controller(session_id=1) is None

    def test_get_session_info_observation(self):
        """观察模式会话 get_session_info 返回 mode='observation'."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="observation", orchestrator=MagicMock())

        info = registry.get_session_info(session_id=1)
        assert info == {"mode": "observation"}

    def test_get_session_info_teacher(self):
        """教师模式会话 get_session_info 返回 mode='teacher'."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="teacher", controller=MagicMock())

        info = registry.get_session_info(session_id=1)
        assert info == {"mode": "teacher"}

    def test_get_session_info_not_found(self):
        """不存在的会话 get_session_info 返回 None."""
        registry = SessionRegistry()

        assert registry.get_session_info(session_id=999) is None

    def test_unregister_clears_session_modes(self):
        """注销会话同时清除 mode 记录."""
        registry = SessionRegistry()
        registry.register(session_id=1, mode="teacher", controller=MagicMock())
        registry.unregister(session_id=1)

        assert registry.get_session_info(session_id=1) is None
        assert registry.get_controller(session_id=1) is None
