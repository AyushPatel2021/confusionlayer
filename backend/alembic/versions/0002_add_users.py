"""add users

Revision ID: 0002_add_users
Revises: 0001_initial_schema
Create Date: 2026-07-14 22:55:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_users"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('admin', 'teacher', 'student')", name="ck_users_role_values"),
        sa.CheckConstraint(
            "(role = 'teacher' AND teacher_id IS NOT NULL AND student_id IS NULL) OR "
            "(role = 'student' AND student_id IS NOT NULL AND teacher_id IS NULL) OR "
            "(role = 'admin' AND teacher_id IS NULL AND student_id IS NULL)",
            name="ck_users_role_profile_link",
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )


def downgrade() -> None:
    op.drop_table("users")
