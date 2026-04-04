"""create student_memories table

Revision ID: 002
Revises: 2c224e826c17
Create Date: 2026-04-04

"""
from collections.abc import Sequence

import sqlalchemy as sa
from schemas.student import StudentAttitude, StudentLevel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: str | Sequence[str] | None = '2c224e826c17'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """创建 student_memories 表."""
    op.create_table(
        'student_memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('student_name', sa.String(length=50), nullable=False),
        sa.Column('level', sa.Enum(StudentLevel), nullable=True),
        sa.Column('attitude', sa.Enum(StudentAttitude), nullable=True),
        sa.Column('learning_ability', sa.Integer(), nullable=True),
        sa.Column('learned_concepts', sa.JSON(), nullable=True),
        sa.Column('confused_points', sa.JSON(), nullable=True),
        sa.Column('questions_asked', sa.JSON(), nullable=True),
        sa.Column('initial_knowledge_level', sa.Float(), nullable=True),
        sa.Column('current_knowledge_level', sa.Float(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['teaching_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_student_memories_session_id', 'student_memories', ['session_id'])
    op.create_index('ix_student_memories_session_student', 'student_memories', ['session_id', 'student_name'])


def downgrade() -> None:
    """删除 student_memories 表."""
    op.drop_index('ix_student_memories_session_student', table_name='student_memories')
    op.drop_index('ix_student_memories_session_id', table_name='student_memories')
    op.drop_table('student_memories')
