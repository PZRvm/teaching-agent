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
