"""persist departments and role-profile data for members

Revision ID: 0013_add_member_departments
Revises: 0012_add_school_operations
Create Date: 2026-07-18 16:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013_add_member_departments"
down_revision: Union[str, None] = "0012_add_school_operations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("department", sa.String(length=80), server_default="Workspace", nullable=False))
    op.add_column("users", sa.Column("profile_data", sa.JSON(), server_default=sa.text("'{}'"), nullable=False))
    op.add_column("invitations", sa.Column("department", sa.String(length=80), server_default="Workspace", nullable=False))
    op.execute("UPDATE users SET department = CASE role WHEN 'teacher' THEN 'Teaching & learning' WHEN 'accountant' THEN 'Accounts' WHEN 'hr' THEN 'HR' WHEN 'school_admin' THEN 'Front-office' WHEN 'parent' THEN 'Family' WHEN 'student' THEN 'Learning' WHEN 'owner' THEN 'School leadership' WHEN 'admin' THEN 'School leadership' ELSE 'Workspace' END")
    op.execute("UPDATE invitations SET department = CASE role WHEN 'teacher' THEN 'Teaching & learning' WHEN 'accountant' THEN 'Accounts' WHEN 'hr' THEN 'HR' WHEN 'school_admin' THEN 'Front-office' WHEN 'parent' THEN 'Family' WHEN 'student' THEN 'Learning' ELSE 'Workspace' END")


def downgrade() -> None:
    op.drop_column("invitations", "department")
    op.drop_column("users", "profile_data")
    op.drop_column("users", "department")
