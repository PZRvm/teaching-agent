"""add receiver column to messages

Revision ID: 004
Revises: 003
Create Date: 2026-04-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "messages", sa.Column("receiver", sa.String(50), nullable=False, server_default="all")
    )


def downgrade() -> None:
    op.drop_column("messages", "receiver")
