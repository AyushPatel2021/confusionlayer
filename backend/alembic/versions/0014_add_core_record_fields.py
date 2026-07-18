"""add richer admission student and employee record fields

Revision ID: 0014_add_core_record_fields
Revises: 0013_add_member_departments
Create Date: 2026-07-18 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_add_core_record_fields"
down_revision: Union[str, None] = "0013_add_member_departments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("admission_applications", sa.Column("source", sa.String(length=80), nullable=True))
    op.add_column("admission_applications", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("students", sa.Column("roll_number", sa.String(length=40), nullable=True))
    op.add_column("students", sa.Column("section", sa.String(length=40), nullable=True))
    op.add_column("students", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("students", sa.Column("guardian_name", sa.String(length=160), nullable=True))
    op.add_column("students", sa.Column("guardian_phone", sa.String(length=40), nullable=True))
    op.add_column("employees", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("employees", sa.Column("join_date", sa.Date(), nullable=True))


def downgrade() -> None:
    for table, column in (("employees", "join_date"), ("employees", "phone"), ("students", "guardian_phone"), ("students", "guardian_name"), ("students", "date_of_birth"), ("students", "section"), ("students", "roll_number"), ("admission_applications", "date_of_birth"), ("admission_applications", "source")):
        op.drop_column(table, column)
