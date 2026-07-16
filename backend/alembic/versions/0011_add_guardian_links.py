"""add guardian_links (parent portal)

Revision ID: 0011_add_guardian_links
Revises: 0010_add_hr
Create Date: 2026-07-16 21:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_add_guardian_links"
down_revision: Union[str, None] = "0010_add_hr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guardian_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("parent_user_id", "student_id", name="uq_guardian_link"),
    )


def downgrade() -> None:
    op.drop_table("guardian_links")
