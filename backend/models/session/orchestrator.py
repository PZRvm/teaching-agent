"""SessionOrchestrator - 观察模式核心控制器."""

import asyncio
from typing import Callable

from models.checkpoint.schemas import Checkpoint


class SessionOrchestrator:
    """观察模式自动教学流程编排器.

    基于检查点系统驱动教学流程：
    - 遍历检查点数组
    - 协调教师和学生 agent 交互
    - 通过 WebSocket 推送状态更新
    - 集成 MemoryManager 记录教学过程
    """

    def __init__(
        self,
        *,
        teacher_agent,
        student_agents: list,
        checkpoint_plan,
        memory_manager,
    ):
        """初始化编排器.

        Args:
            teacher_agent: 教师 agent
            student_agents: 学生 agent 列表
            checkpoint_plan: 检查点计划
            memory_manager: 记忆管理器
        """
        self.teacher_agent = teacher_agent
        self.student_agents = student_agents
        self.checkpoint_plan = checkpoint_plan
        self.memory_manager = memory_manager

        # WebSocket 推送回调（可选，用于测试）
        self._ws_push_callback: Callable | None = None

    def set_ws_push_callback(self, callback: Callable) -> None:
        """设置 WebSocket 推送回调（用于测试）."""
        self._ws_push_callback = callback

    async def run_autonomous_session(self) -> None:
        """运行自动教学会话（基于检查点）.

        遍历所有检查点，对每个检查点执行教学流程：
        - 灌输式: TEACHING → COMPLETE
        - 启发式/讨论式: TEACHING → QUESTIONS → COMPLETE

        最后一个检查点完成后布置作业和收集反馈。
        """
        num_checkpoints = len(self.checkpoint_plan.checkpoints)

        for i, checkpoint in enumerate(self.checkpoint_plan.checkpoints):
            # 更新当前索引
            self.checkpoint_plan.current_index = i

            # 教授当前检查点
            await self._teach_checkpoint(checkpoint)

        # 所有检查点完成后，布置作业和收集反馈
        await self._assign_homework()
        await self._collect_homework_and_feedback()

    async def _teach_checkpoint(self, checkpoint: Checkpoint) -> None:
        """教授单个检查点.

        Args:
            checkpoint: 当前检查点
        """
        # TODO: 实现教学逻辑
        pass

    async def _assign_homework(self) -> None:
        """布置作业."""
        # TODO: 实现作业布置逻辑
        pass

    async def _collect_homework_and_feedback(self) -> None:
        """收集作业和反馈."""
        # TODO: 实现作业收集和反馈逻辑
        pass
