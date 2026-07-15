"""add mastery history

Revision ID: 0004_add_mastery_history
Revises: 0003_add_ai_call_usage
Create Date: 2026-07-15 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_add_mastery_history"
down_revision: Union[str, None] = "0003_add_ai_call_usage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mastery_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mastery", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.Date(), nullable=False),
        sa.CheckConstraint("mastery >= 0 AND mastery <= 1", name="ck_mastery_history_range"),
        sa.UniqueConstraint("student_id", "concept_id", "recorded_at", name="uq_mastery_history_point"),
    )


def downgrade() -> None:
    op.drop_table("mastery_history")
