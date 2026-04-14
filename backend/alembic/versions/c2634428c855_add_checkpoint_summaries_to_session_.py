"""add checkpoint_summaries to session_memories

Revision ID: c2634428c855
Revises: 4934dd3d406c
Create Date: 2026-04-13 16:24:20.321822

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2634428c855"
down_revision: str | Sequence[str] | None = "4934dd3d406c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("session_memories", sa.Column("checkpoint_summaries", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("session_memories", "checkpoint_summaries")
