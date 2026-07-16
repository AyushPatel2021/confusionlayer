"""add users.name

Revision ID: 0006_add_user_name
Revises: 0005_add_multitenancy
Create Date: 2026-07-16 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_add_user_name"
down_revision: Union[str, None] = "0005_add_multitenancy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("name", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "name")
