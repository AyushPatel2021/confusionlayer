"""add subjects.org_id (org-authored curriculum)

Revision ID: 0007_add_subject_org
Revises: 0006_add_user_name
Create Date: 2026-07-16 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_add_subject_org"
down_revision: Union[str, None] = "0006_add_user_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("subjects") as batch:
        batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_subjects_org_id", "organizations", ["org_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    with op.batch_alter_table("subjects") as batch:
        batch.drop_constraint("fk_subjects_org_id", type_="foreignkey")
        batch.drop_column("org_id")
