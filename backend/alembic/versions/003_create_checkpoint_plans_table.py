"""create checkpoint_plans table

Revision ID: 003
Revises: 002
Create Date: 2026-04-05

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 checkpoint_plans 表."""
    op.create_table(
        "checkpoint_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("plan_data", sa.Text(), nullable=False),  # SQLite 使用 TEXT 存储 JSON
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["teaching_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checkpoint_plans_session_id", "checkpoint_plans", ["session_id"])


def downgrade() -> None:
    """删除 checkpoint_plans 表."""
    op.drop_index("ix_checkpoint_plans_session_id", table_name="checkpoint_plans")
    op.drop_table("checkpoint_plans")
