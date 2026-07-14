"""initial schema

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-07-14 22:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
    )
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
    )
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("board", sa.String(length=80), nullable=False),
        sa.Column("class_level", sa.String(length=80), nullable=False),
        sa.UniqueConstraint("name", "board", "class_level", name="uq_subject_identity"),
    )
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("subject_id", "order", name="uq_chapter_subject_order"),
        sa.UniqueConstraint("subject_id", "title", name="uq_chapter_subject_title"),
    )
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
    )
    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.UniqueConstraint("chapter_id", "order", name="uq_concept_chapter_order"),
        sa.UniqueConstraint("chapter_id", "title", name="uq_concept_chapter_title"),
    )
    op.create_table(
        "chapter_unlocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unlocked_by", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("classroom_id", "chapter_id", name="uq_chapter_unlock_classroom_chapter"),
    )
    op.create_table(
        "classroom_students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("classroom_id", "student_id", name="uq_classroom_student"),
    )
    op.create_table(
        "concept_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prerequisite_concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weight", sa.Float(), server_default="1.0", nullable=False),
        sa.CheckConstraint("concept_id <> prerequisite_concept_id", name="ck_concept_edge_not_self"),
        sa.UniqueConstraint("concept_id", "prerequisite_concept_id", name="uq_concept_edge_pair"),
    )
    op.create_table(
        "confusion_briefs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("classroom_id", sa.Integer(), sa.ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_text", sa.Text(), nullable=False),
        sa.Column("affected_student_count", sa.Integer(), nullable=False),
        sa.Column("misconception_breakdown", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "forecast_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("predicted_difficulty", sa.Float(), nullable=False),
        sa.Column("contributing_concepts", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("predicted_difficulty >= 0 AND predicted_difficulty <= 1", name="ck_forecast_difficulty_range"),
    )
    op.create_table(
        "mastery_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quiz_accuracy_score", sa.Float(), nullable=False),
        sa.Column("open_answer_score", sa.Float(), nullable=False),
        sa.Column("misconception_recurrence", sa.Float(), nullable=False),
        sa.Column("retention_score", sa.Float(), nullable=False),
        sa.Column("computed_mastery", sa.Float(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=False),
        sa.CheckConstraint("quiz_accuracy_score >= 0 AND quiz_accuracy_score <= 1", name="ck_mastery_quiz_range"),
        sa.CheckConstraint("open_answer_score >= 0 AND open_answer_score <= 1", name="ck_mastery_open_range"),
        sa.CheckConstraint("misconception_recurrence >= 0 AND misconception_recurrence <= 1", name="ck_mastery_recurrence_range"),
        sa.CheckConstraint("retention_score >= 0 AND retention_score <= 1", name="ck_mastery_retention_range"),
        sa.CheckConstraint("computed_mastery >= 0 AND computed_mastery <= 1", name="ck_mastery_computed_range"),
        sa.UniqueConstraint("student_id", "concept_id", name="uq_mastery_student_concept"),
    )
    op.create_table(
        "misconception_taxonomy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.UniqueConstraint("concept_id", "code", name="uq_taxonomy_concept_code"),
    )
    op.create_table(
        "teach_back_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_explanation", sa.Text(), nullable=False),
        sa.Column("clarity_score", sa.Float(), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=False),
        sa.Column("gpt_feedback", sa.Text(), nullable=False),
        sa.CheckConstraint("clarity_score >= 0 AND clarity_score <= 1", name="ck_teach_back_clarity_range"),
        sa.CheckConstraint("accuracy_score >= 0 AND accuracy_score <= 1", name="ck_teach_back_accuracy_range"),
    )
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept_id", sa.Integer(), sa.ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("student_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("misconception_code", sa.String(length=120), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_quiz_confidence_range"),
        sa.CheckConstraint("mode IN ('quiz', 'exam', 'teach_back')", name="ck_quiz_mode_values"),
    )


def downgrade() -> None:
    op.drop_table("quiz_attempts")
    op.drop_table("teach_back_attempts")
    op.drop_table("misconception_taxonomy")
    op.drop_table("mastery_records")
    op.drop_table("forecast_records")
    op.drop_table("confusion_briefs")
    op.drop_table("concept_edges")
    op.drop_table("classroom_students")
    op.drop_table("chapter_unlocks")
    op.drop_table("concepts")
    op.drop_table("classrooms")
    op.drop_table("chapters")
    op.drop_table("subjects")
    op.drop_table("students")
    op.drop_table("teachers")
