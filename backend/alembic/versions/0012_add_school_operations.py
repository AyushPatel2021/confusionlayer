"""add school operations, organization preferences, and notifications

Revision ID: 0012_add_school_operations
Revises: 0011_add_guardian_links
Create Date: 2026-07-18 13:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012_add_school_operations"
down_revision: Union[str, None] = "0011_add_guardian_links"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("logo_url", sa.String(length=500), nullable=True))
    op.add_column("organizations", sa.Column("timezone", sa.String(length=80), server_default="Asia/Kolkata", nullable=False))
    op.add_column("organizations", sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False))
    op.create_table("attendance_records", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False), sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False), sa.Column("attendance_date", sa.Date(), nullable=False), sa.Column("status", sa.String(length=20), nullable=False), sa.Column("note", sa.String(length=255), nullable=True), sa.Column("recorded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.CheckConstraint("status IN ('present', 'absent', 'late', 'excused')", name="ck_attendance_status"), sa.UniqueConstraint("classroom_id", "student_id", "attendance_date", name="uq_attendance_classroom_student_date"))
    op.create_table("timetable_entries", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False), sa.Column("weekday", sa.Integer(), nullable=False), sa.Column("starts_at", sa.String(length=5), nullable=False), sa.Column("ends_at", sa.String(length=5), nullable=False), sa.Column("room", sa.String(length=80), nullable=True), sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_timetable_weekday"))
    op.create_table("library_books", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(length=240), nullable=False), sa.Column("author", sa.String(length=160), nullable=True), sa.Column("isbn", sa.String(length=32), nullable=True), sa.Column("copies_total", sa.Integer(), server_default="1", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint("org_id", "isbn", name="uq_library_book_isbn"))
    op.create_table("library_loans", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("book_id", sa.Integer(), sa.ForeignKey("library_books.id", ondelete="CASCADE"), nullable=False), sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False), sa.Column("due_date", sa.Date(), nullable=True), sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("transport_routes", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(length=160), nullable=False), sa.Column("vehicle_label", sa.String(length=120), nullable=True), sa.Column("driver_name", sa.String(length=160), nullable=True), sa.Column("stops", sa.JSON(), nullable=False), sa.UniqueConstraint("org_id", "name", name="uq_transport_route_name"))
    op.create_table("student_transport_assignments", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("org_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False), sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False), sa.Column("route_id", sa.Integer(), sa.ForeignKey("transport_routes.id", ondelete="CASCADE"), nullable=False), sa.Column("stop_name", sa.String(length=160), nullable=True), sa.UniqueConstraint("student_id", name="uq_student_transport_assignment"))
    op.create_table("notifications", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(length=160), nullable=False), sa.Column("body", sa.String(length=500), nullable=True), sa.Column("href", sa.String(length=255), nullable=True), sa.Column("read_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    for table in ("notifications", "student_transport_assignments", "transport_routes", "library_loans", "library_books", "timetable_entries", "attendance_records"):
        op.drop_table(table)
    op.drop_column("organizations", "currency")
    op.drop_column("organizations", "timezone")
    op.drop_column("organizations", "logo_url")
