"""Checkpoint 持久化服务."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.checkpoint.schemas import CheckpointPlan, CheckpointState
from orm.checkpoint_plan import CheckpointPlanModel


class CheckpointPlanPersistence:
    """检查点计划持久化服务.

    提供数据库读写操作，支持：
    - 保存新计划
    - 加载计划
    - 更新检查点状态
    - 推进检查点索引
    - 删除计划
    """

    def __init__(self, db_session: AsyncSession):
        """初始化服务.

        Args:
            db_session: 异步数据库会话
        """
        self.db_session = db_session

    async def save_plan(self, session_id: int, plan: CheckpointPlan) -> int:
        """保存检查点计划到数据库.

        Args:
            session_id: 教学会话 ID
            plan: 检查点计划

        Returns:
            创建的记录 ID
        """
        plan_record = CheckpointPlanModel(
            session_id=session_id,
            plan_data=plan.model_dump(),
        )

        self.db_session.add(plan_record)
        await self.db_session.commit()
        await self.db_session.refresh(plan_record)

        return plan_record.id

    async def update_plan(self, session_id: int, plan: CheckpointPlan) -> None:
        """更新检查点计划.

        Args:
            session_id: 教学会话 ID
            plan: 新的检查点计划

        Raises:
            ValueError: 如果检查点计划不存在或教学已开始
        """
        result = await self.db_session.execute(
            select(CheckpointPlanModel)
            .where(CheckpointPlanModel.session_id == session_id)
            .with_for_update()  # Lock row to prevent race conditions
        )
        record = result.scalar_one_or_none()

        if record is None:
            raise ValueError(f"Checkpoint plan for session {session_id} not found")

        # 验证现有计划的所有检查点都是 PENDING 状态（教学未开始）
        existing_plan_data = record.plan_data
        for checkpoint in existing_plan_data.get("checkpoints", []):
            if checkpoint.get("state") != CheckpointState.PENDING.value:
                raise ValueError("只能在教学开始前编辑检查点")

        new_plan_data = plan.model_dump()
        record.update_plan_data(new_plan_data)
        await self.db_session.commit()

    async def load_plan(self, session_id: int) -> CheckpointPlan | None:
        """根据 session_id 加载检查点计划.

        Args:
            session_id: 教学会话 ID

        Returns:
            检查点计划，如果不存在则返回 None
        """
        result = await self.db_session.execute(
            select(CheckpointPlanModel).where(CheckpointPlanModel.session_id == session_id)
        )
        record = result.scalar_one_or_none()

        if record is None:
            return None

        return CheckpointPlan(**record.plan_data)

    async def update_checkpoint_state(
        self, session_id: int, checkpoint_index: int, new_state: CheckpointState
    ) -> None:
        """更新指定检查点的状态.

        Args:
            session_id: 教学会话 ID
            checkpoint_index: 检查点索引
            new_state: 新状态

        Raises:
            ValueError: 如果检查点计划不存在
        """
        result = await self.db_session.execute(
            select(CheckpointPlanModel)
            .where(CheckpointPlanModel.session_id == session_id)
            .with_for_update()  # Lock row to prevent race conditions
        )
        record = result.scalar_one_or_none()

        if record is None:
            raise ValueError(f"Checkpoint plan for session {session_id} not found")

        # 更新 JSON 字段中的状态
        plan_data = record.plan_data.copy()
        plan_data["checkpoints"][checkpoint_index]["state"] = new_state.value

        # 使用 update_plan_data 触发 SQLAlchemy 变更跟踪
        record.update_plan_data(plan_data)
        await self.db_session.commit()

    async def advance_checkpoint(self, session_id: int) -> None:
        """推进到下一个检查点.

        将当前索引加 1，并将新当前检查点状态设为 TEACHING。

        Args:
            session_id: 教学会话 ID

        Raises:
            ValueError: 如果检查点计划不存在
            IndexError: 如果已经到达最后一个检查点
        """
        result = await self.db_session.execute(
            select(CheckpointPlanModel)
            .where(CheckpointPlanModel.session_id == session_id)
            .with_for_update()  # Lock row to prevent race conditions
        )
        record = result.scalar_one_or_none()

        if record is None:
            raise ValueError(f"Checkpoint plan for session {session_id} not found")

        plan_data = record.plan_data.copy()
        new_index = plan_data["current_index"] + 1

        if new_index >= len(plan_data["checkpoints"]):
            raise IndexError("Cannot advance beyond last checkpoint")

        plan_data["current_index"] = new_index
        plan_data["checkpoints"][new_index]["state"] = CheckpointState.TEACHING.value

        record.update_plan_data(plan_data)
        await self.db_session.commit()

    async def delete_plan(self, session_id: int) -> None:
        """删除指定会话的检查点计划.

        Args:
            session_id: 教学会话 ID
        """
        await self.db_session.execute(
            delete(CheckpointPlanModel).where(CheckpointPlanModel.session_id == session_id)
        )
        await self.db_session.commit()
