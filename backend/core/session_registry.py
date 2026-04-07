from __future__ import annotations

"""会话注册表 — 映射 session_id 到运行中的 orchestrator/controller."""


class SessionRegistry:
    """全局会话注册表.

    将 session_id 映射到对应的 SessionOrchestrator 或 TeacherSessionController 实例。
    用于 WebSocket 端点根据 session_id 查找业务逻辑实例。
    """

    def __init__(self) -> None:
        self._orchestrators: dict[int, object] = {}
        self._controllers: dict[int, object] = {}

    def register(
        self,
        *,
        session_id: int,
        mode: str,
        orchestrator: object | None = None,
        controller: object | None = None,
    ) -> None:
        """注册会话实例."""
        if mode == "observation" and orchestrator is not None:
            self._orchestrators[session_id] = orchestrator
        elif mode == "teacher" and controller is not None:
            self._controllers[session_id] = controller

    def unregister(self, session_id: int) -> None:
        """注销会话."""
        self._orchestrators.pop(session_id, None)
        self._controllers.pop(session_id, None)

    def get_orchestrator(self, session_id: int) -> object | None:
        """获取观察模式 orchestrator."""
        return self._orchestrators.get(session_id)

    def get_controller(self, session_id: int) -> object | None:
        """获取教师模式 controller."""
        return self._controllers.get(session_id)
