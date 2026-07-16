"""add multi-tenancy: organizations, plans, subscriptions, invitations, resets, audit

Revision ID: 0005_add_multitenancy
Revises: 0004_add_mastery_history
Create Date: 2026-07-16 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_add_multitenancy"
down_revision: Union[str, None] = "0004_add_mastery_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("segment", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("segment IN ('school', 'institute', 'individual')", name="ck_org_segment_values"),
        sa.UniqueConstraint("slug", name="uq_org_slug"),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("segment", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.CheckConstraint("segment IN ('school', 'institute', 'individual')", name="ck_plan_segment_values"),
        sa.CheckConstraint("price_cents >= 0", name="ck_plan_price_nonnegative"),
        sa.UniqueConstraint("code", name="uq_plan_code"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("provider_customer_id", sa.String(length=120), nullable=True),
        sa.Column("provider_subscription_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('trialing', 'active', 'past_due', 'canceled')", name="ck_subscription_status_values"),
        sa.UniqueConstraint("org_id", name="uq_subscription_org"),
    )

    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("invited_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token", name="uq_invitation_token"),
    )

    op.create_table(
        "password_resets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(length=120), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token", name="uq_password_reset_token"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Users: add org + status + verification, widen role constraints.
    # Batch mode keeps this portable (normal ALTER on Postgres, table-rebuild on SQLite).
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("status", sa.String(length=20), server_default="active", nullable=False))
        batch.add_column(sa.Column("email_verified", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch.drop_constraint("ck_users_role_values", type_="check")
        batch.drop_constraint("ck_users_role_profile_link", type_="check")
        batch.create_check_constraint(
            "ck_users_role_values",
            "role IN ('admin', 'owner', 'school_admin', 'accountant', 'hr', 'teacher', 'student', 'parent', 'platform_admin')",
        )
        batch.create_check_constraint(
            "ck_users_role_profile_link",
            "(role = 'teacher' AND teacher_id IS NOT NULL AND student_id IS NULL) OR "
            "(role = 'student' AND student_id IS NOT NULL AND teacher_id IS NULL) OR "
            "(role NOT IN ('teacher', 'student'))",
        )
        batch.create_foreign_key("fk_users_org_id", "organizations", ["org_id"], ["id"], ondelete="CASCADE")

    with op.batch_alter_table("classrooms") as batch:
        batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_classrooms_org_id", "organizations", ["org_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    with op.batch_alter_table("classrooms") as batch:
        batch.drop_constraint("fk_classrooms_org_id", type_="foreignkey")
        batch.drop_column("org_id")

    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_org_id", type_="foreignkey")
        batch.drop_constraint("ck_users_role_profile_link", type_="check")
        batch.drop_constraint("ck_users_role_values", type_="check")
        batch.create_check_constraint("ck_users_role_values", "role IN ('admin', 'teacher', 'student')")
        batch.create_check_constraint(
            "ck_users_role_profile_link",
            "(role = 'teacher' AND teacher_id IS NOT NULL AND student_id IS NULL) OR "
            "(role = 'student' AND student_id IS NOT NULL AND teacher_id IS NULL) OR "
            "(role = 'admin' AND teacher_id IS NULL AND student_id IS NULL)",
        )
        batch.drop_column("email_verified")
        batch.drop_column("status")
        batch.drop_column("org_id")

    op.drop_table("audit_logs")
    op.drop_table("password_resets")
    op.drop_table("invitations")
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("organizations")
