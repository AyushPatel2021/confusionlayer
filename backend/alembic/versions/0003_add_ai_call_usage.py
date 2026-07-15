"""add ai call usage

Revision ID: 0003_add_ai_call_usage
Revises: 0002_add_users
Create Date: 2026-07-15 11:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_ai_call_usage"
down_revision: Union[str, None] = "0002_add_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_call_usage",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("call_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("call_count >= 0", name="ck_ai_call_usage_count_nonnegative"),
        sa.UniqueConstraint("user_id", "usage_date", name="uq_ai_call_usage_user_date"),
    )


def downgrade() -> None:
    op.drop_table("ai_call_usage")
