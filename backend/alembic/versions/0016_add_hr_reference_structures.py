"""add HR designation and salary structures

Revision ID: 0016_add_hr_reference_structures
Revises: 0015_add_invoice_line_items
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_add_hr_reference_structures"
down_revision: Union[str, None] = "0015_add_invoice_line_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("designations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(length=120), nullable=False), sa.Column("department", sa.String(length=80)), sa.UniqueConstraint("org_id", "name", name="uq_designation_org_name"))
    op.create_table("salary_structures", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(length=120), nullable=False), sa.Column("monthly_amount_cents", sa.Integer(), nullable=False), sa.CheckConstraint("monthly_amount_cents >= 0", name="ck_salary_structure_amount"), sa.UniqueConstraint("org_id", "name", name="uq_salary_structure_org_name"))
    op.add_column("employees", sa.Column("designation_id", sa.Integer(), sa.ForeignKey("designations.id", ondelete="SET NULL")))
    op.add_column("employees", sa.Column("salary_structure_id", sa.Integer(), sa.ForeignKey("salary_structures.id", ondelete="SET NULL")))
    op.add_column("employees", sa.Column("employment_type", sa.String(length=30), server_default="full_time", nullable=False))


def downgrade() -> None:
    op.drop_column("employees", "employment_type")
    op.drop_column("employees", "salary_structure_id")
    op.drop_column("employees", "designation_id")
    op.drop_table("salary_structures")
    op.drop_table("designations")
