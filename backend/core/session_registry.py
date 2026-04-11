from __future__ import annotations

from typing import TYPE_CHECKING

"""会话注册表 — 映射 session_id 到运行中的 orchestrator/controller.

用于 WebSocket 端点根据 session_id 查找业务逻辑实例。
"""

if TYPE_CHECKING:
    from models.session.services.observation_service import SessionOrchestrator
    from models.session.services.teacher_service import TeacherSessionController


class SessionRegistry:
    """全局会话注册表.

    将 session_id 映射到对应的 SessionOrchestrator 或 TeacherSessionController 实例。
    用于 WebSocket 端点根据 session_id 查找业务逻辑实例。
    """

    def __init__(self) -> None:
        self._orchestrators: dict[int, SessionOrchestrator] = {}
        self._controllers: dict[int, TeacherSessionController] = {}
        self._session_modes: dict[int, str] = {}

    def register(
        self,
        *,
        session_id: int,
        mode: str,
        orchestrator: SessionOrchestrator | None = None,
        controller: TeacherSessionController | None = None,
    ) -> None:
        """注册会话实例.

        支持仅注册 mode（不传 orchestrator/controller），后续通过
        register_orchestrator() 延迟注册。
        """
        self._session_modes[session_id] = mode
        if mode == "observation" and orchestrator is not None:
            self._orchestrators[session_id] = orchestrator
        elif mode == "teacher" and controller is not None:
            self._controllers[session_id] = controller

    def register_orchestrator(self, session_id: int, orchestrator: SessionOrchestrator) -> None:
        """延迟注册 orchestrator（初始化完成后调用）."""
        self._orchestrators[session_id] = orchestrator

    def unregister(self, session_id: int) -> None:
        """注销会话."""
        self._orchestrators.pop(session_id, None)
        self._controllers.pop(session_id, None)
        self._session_modes.pop(session_id, None)

    def get_orchestrator(self, session_id: int) -> SessionOrchestrator | None:
        """获取观察模式 orchestrator."""
        return self._orchestrators.get(session_id)

    def get_controller(self, session_id: int) -> TeacherSessionController | None:
        """获取教师模式 controller."""
        return self._controllers.get(session_id)

    def get_session_info(self, session_id: int) -> dict[str, str] | None:
        """获取会话模式信息.

        Returns:
            {"mode": "observation"} 或 {"mode": "teacher"}，不存在则返回 None
        """
        mode = self._session_modes.get(session_id)
        if mode is None:
            return None
        return {"mode": mode}


# 模块级单例实例（应用生命周期内唯一）
_session_registry: SessionRegistry | None = None


def get_session_registry() -> SessionRegistry:
    """获取全局 SessionRegistry 实例."""
    global _session_registry
    if _session_registry is None:
        _session_registry = SessionRegistry()
    return _session_registry


def set_session_registry(registry: SessionRegistry) -> None:
    """设置全局 SessionRegistry 实例（用于测试注入）."""
    global _session_registry
    _session_registry = registry
