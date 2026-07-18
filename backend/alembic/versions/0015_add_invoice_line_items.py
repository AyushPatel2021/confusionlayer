"""add invoice line items

Revision ID: 0015_add_invoice_line_items
Revises: 0014_add_core_record_fields
Create Date: 2026-07-18 19:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015_add_invoice_line_items"
down_revision: Union[str, None] = "0014_add_core_record_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(length=160), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount_cents >= 0", name="ck_invoice_line_item_amount"),
    )


def downgrade() -> None:
    op.drop_table("invoice_line_items")
