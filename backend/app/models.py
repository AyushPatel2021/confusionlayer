from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# Go-to-market segments; select which module bundle an org uses.
ORG_SEGMENTS = ("school", "institute", "individual")


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        CheckConstraint("segment IN ('school', 'institute', 'individual')", name="ck_org_segment_values"),
        UniqueConstraint("slug", name="uq_org_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    segment: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="organization")
    classrooms: Mapped[list[Classroom]] = relationship(back_populates="organization")
    subscription: Mapped[Subscription | None] = relationship(back_populates="organization")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (
        CheckConstraint("segment IN ('school', 'institute', 'individual')", name="ck_plan_segment_values"),
        CheckConstraint("price_cents >= 0", name="ck_plan_price_nonnegative"),
        UniqueConstraint("code", name="uq_plan_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    segment: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    limits: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    features: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('trialing', 'active', 'past_due', 'canceled')", name="ck_subscription_status_values"
        ),
        UniqueConstraint("org_id", name="uq_subscription_org"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="subscription")
    plan: Mapped[Plan] = relationship()


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (UniqueConstraint("token", name="uq_invitation_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    token: Mapped[str] = mapped_column(String(120), nullable=False)
    invited_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    __table_args__ = (UniqueConstraint("token", name="uq_password_reset_token"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(120), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audit_metadata: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


ADMISSION_STATUSES = ("applied", "reviewing", "accepted", "rejected", "enrolled")


class AdmissionApplication(Base):
    __tablename__ = "admission_applications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('applied', 'reviewing', 'accepted', 'rejected', 'enrolled')", name="ck_admission_status_values"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    applicant_name: Mapped[str] = mapped_column(String(160), nullable=False)
    applicant_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="applied", server_default="applied", nullable=False)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    classrooms: Mapped[list[Classroom]] = relationship(back_populates="teacher")
    user: Mapped[User | None] = relationship(back_populates="teacher")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    classrooms: Mapped[list[ClassroomStudent]] = relationship(back_populates="student")
    mastery_records: Mapped[list[MasteryRecord]] = relationship(back_populates="student")
    user: Mapped[User | None] = relationship(back_populates="student")


# Roles a user can hold in an organization (plus the cross-org platform admin).
USER_ROLES = ("admin", "owner", "school_admin", "accountant", "hr", "teacher", "student", "parent", "platform_admin")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'owner', 'school_admin', 'accountant', 'hr', 'teacher', 'student', 'parent', 'platform_admin')",
            name="ck_users_role_values",
        ),
        CheckConstraint(
            "(role = 'teacher' AND teacher_id IS NOT NULL AND student_id IS NULL) OR "
            "(role = 'student' AND student_id IS NOT NULL AND teacher_id IS NULL) OR "
            "(role NOT IN ('teacher', 'student'))",
            name="ck_users_role_profile_link",
        ),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active", nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization: Mapped[Organization | None] = relationship(back_populates="users")
    teacher: Mapped[Teacher | None] = relationship(back_populates="user")
    student: Mapped[Student | None] = relationship(back_populates="user")
    ai_call_usage: Mapped[list[AiCallUsage]] = relationship(back_populates="user")


class AiCallUsage(Base):
    __tablename__ = "ai_call_usage"
    __table_args__ = (
        CheckConstraint("call_count >= 0", name="ck_ai_call_usage_count_nonnegative"),
        UniqueConstraint("user_id", "usage_date", name="uq_ai_call_usage_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    usage_date: Mapped[date] = mapped_column(Date, nullable=False)
    call_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="ai_call_usage")


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("name", "board", "class_level", name="uq_subject_identity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    board: Mapped[str] = mapped_column(String(80), nullable=False)
    class_level: Mapped[str] = mapped_column(String(80), nullable=False)

    chapters: Mapped[list[Chapter]] = relationship(back_populates="subject")
    classrooms: Mapped[list[Classroom]] = relationship(back_populates="subject")


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("subject_id", "order", name="uq_chapter_subject_order"),
        UniqueConstraint("subject_id", "title", name="uq_chapter_subject_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    subject: Mapped[Subject] = relationship(back_populates="chapters")
    concepts: Mapped[list[Concept]] = relationship(back_populates="chapter")


class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (
        UniqueConstraint("chapter_id", "order", name="uq_concept_chapter_order"),
        UniqueConstraint("chapter_id", "title", name="uq_concept_chapter_title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    chapter: Mapped[Chapter] = relationship(back_populates="concepts")
    taxonomy: Mapped[list[MisconceptionTaxonomy]] = relationship(back_populates="concept")


class ConceptEdge(Base):
    __tablename__ = "concept_edges"
    __table_args__ = (
        CheckConstraint("concept_id <> prerequisite_concept_id", name="ck_concept_edge_not_self"),
        UniqueConstraint("concept_id", "prerequisite_concept_id", name="uq_concept_edge_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    prerequisite_concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default="1.0", nullable=False)


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    organization: Mapped[Organization | None] = relationship(back_populates="classrooms")
    teacher: Mapped[Teacher] = relationship(back_populates="classrooms")
    subject: Mapped[Subject] = relationship(back_populates="classrooms")
    students: Mapped[list[ClassroomStudent]] = relationship(back_populates="classroom")


class ClassroomStudent(Base):
    __tablename__ = "classroom_students"
    __table_args__ = (UniqueConstraint("classroom_id", "student_id", name="uq_classroom_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    classroom: Mapped[Classroom] = relationship(back_populates="students")
    student: Mapped[Student] = relationship(back_populates="classrooms")


class ChapterUnlock(Base):
    __tablename__ = "chapter_unlocks"
    __table_args__ = (UniqueConstraint("classroom_id", "chapter_id", name="uq_chapter_unlock_classroom_chapter"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    unlocked_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class MisconceptionTaxonomy(Base):
    __tablename__ = "misconception_taxonomy"
    __table_args__ = (UniqueConstraint("concept_id", "code", name="uq_taxonomy_concept_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    concept: Mapped[Concept] = relationship(back_populates="taxonomy")


class MasteryRecord(Base):
    __tablename__ = "mastery_records"
    __table_args__ = (
        CheckConstraint("quiz_accuracy_score >= 0 AND quiz_accuracy_score <= 1", name="ck_mastery_quiz_range"),
        CheckConstraint("open_answer_score >= 0 AND open_answer_score <= 1", name="ck_mastery_open_range"),
        CheckConstraint("misconception_recurrence >= 0 AND misconception_recurrence <= 1", name="ck_mastery_recurrence_range"),
        CheckConstraint("retention_score >= 0 AND retention_score <= 1", name="ck_mastery_retention_range"),
        CheckConstraint("computed_mastery >= 0 AND computed_mastery <= 1", name="ck_mastery_computed_range"),
        UniqueConstraint("student_id", "concept_id", name="uq_mastery_student_concept"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    quiz_accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    open_answer_score: Mapped[float] = mapped_column(Float, nullable=False)
    misconception_recurrence: Mapped[float] = mapped_column(Float, nullable=False)
    retention_score: Mapped[float] = mapped_column(Float, nullable=False)
    computed_mastery: Mapped[float] = mapped_column(Float, nullable=False)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    next_review_date: Mapped[date] = mapped_column(Date, nullable=False)

    student: Mapped[Student] = relationship(back_populates="mastery_records")


class MasteryHistory(Base):
    __tablename__ = "mastery_history"
    __table_args__ = (
        CheckConstraint("mastery >= 0 AND mastery <= 1", name="ck_mastery_history_range"),
        UniqueConstraint("student_id", "concept_id", "recorded_at", name="uq_mastery_history_point"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    mastery: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[date] = mapped_column(Date, nullable=False)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_quiz_confidence_range"),
        CheckConstraint("mode IN ('quiz', 'exam', 'teach_back')", name="ck_quiz_mode_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    student_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    misconception_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[str] = mapped_column(String(40), nullable=False)


class TeachBackAttempt(Base):
    __tablename__ = "teach_back_attempts"
    __table_args__ = (
        CheckConstraint("clarity_score >= 0 AND clarity_score <= 1", name="ck_teach_back_clarity_range"),
        CheckConstraint("accuracy_score >= 0 AND accuracy_score <= 1", name="ck_teach_back_accuracy_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    student_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    clarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_score: Mapped[float] = mapped_column(Float, nullable=False)
    gpt_feedback: Mapped[str] = mapped_column(Text, nullable=False)


class ForecastRecord(Base):
    __tablename__ = "forecast_records"
    __table_args__ = (CheckConstraint("predicted_difficulty >= 0 AND predicted_difficulty <= 1", name="ck_forecast_difficulty_range"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    predicted_difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    contributing_concepts: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ConfusionBrief(Base):
    __tablename__ = "confusion_briefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False)
    generated_text: Mapped[str] = mapped_column(Text, nullable=False)
    affected_student_count: Mapped[int] = mapped_column(Integer, nullable=False)
    misconception_breakdown: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
