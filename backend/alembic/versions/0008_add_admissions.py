"""add admission_applications

Revision ID: 0008_add_admissions
Revises: 0007_add_subject_org
Create Date: 2026-07-16 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_add_admissions"
down_revision: Union[str, None] = "0007_add_subject_org"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admission_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("applicant_name", sa.String(length=160), nullable=False),
        sa.Column("applicant_email", sa.String(length=255), nullable=True),
        sa.Column("grade", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="applied", nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('applied', 'reviewing', 'accepted', 'rejected', 'enrolled')", name="ck_admission_status_values"),
    )


def downgrade() -> None:
    op.drop_table("admission_applications")
