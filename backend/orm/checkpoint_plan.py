"""Checkpoint 持久化 ORM 模型"""

from sqlalchemy import JSON, Integer
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CheckpointPlanModel(Base, AsyncAttrs):
    """检查点计划表"""

    __tablename__ = "checkpoint_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_data: Mapped[dict] = mapped_column(JSON)

    def update_plan_data(self, new_data: dict) -> None:
        """Update plan_data and flag as modified for SQLAlchemy.

        Use this method when modifying the plan_data dict in place to ensure
        SQLAlchemy tracks the changes. Direct dict modifications won't be
        automatically detected.

        Args:
            new_data: The new plan_data dict to set
        """
        self.plan_data = new_data
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(self, "plan_data")
