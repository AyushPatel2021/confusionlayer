from __future__ import annotations

import os
from datetime import date, datetime, timezone
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-parent-admin-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import RegisterRequest, register_org
from app.main import (
    GuardianLinkRequest,
    InvoiceCreateRequest,
    admin_list_orgs,
    admin_usage,
    create_invoice,
    link_guardian,
    list_children,
)
from app.models import AttendanceRecord, Base, Chapter, Concept, MasteryRecord, QuizAttempt, Student, Subject, TeachBackAttempt, User
from app.seed import backfill_tenancy


class ParentAdminTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        backfill_tenancy(self.db)
        self.owner, self.org = register_org(
            self.db, RegisterRequest(org_name="Green Valley", segment="school", email="o@gv.test", password="password123", name="Head")
        )
        self.parent = User(org_id=self.org.id, email="p@gv.test", password_hash="x", role="parent", name="Parent")
        self.student = Student(name="Child A")
        self.db.add_all([self.parent, self.student])
        self.db.flush()
        self.student_member = User(org_id=self.org.id, email="child@gv.test", password_hash="x", role="student", name="Child A", student_id=self.student.id)
        self.db.add(self.student_member)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    # ---- M10 ----

    def test_link_and_view_child_with_outstanding_fees(self) -> None:
        create_invoice(InvoiceCreateRequest(recipient_name="Child A", amount_cents=5000, student_id=self.student.id), current_user=self.owner, db=self.db)
        subject = Subject(org_id=self.org.id, name="Science", board="CBSE", class_level="10")
        chapter = Chapter(title="Chemistry", order=1)
        strong = Concept(title="Acids and Bases", order=1)
        weak = Concept(title="Ionic Bonding", order=2)
        chapter.concepts.extend([strong, weak])
        subject.chapters.append(chapter)
        self.db.add(subject)
        self.db.flush()
        self.db.add_all([
            MasteryRecord(student_id=self.student.id, concept_id=strong.id, quiz_accuracy_score=0.9, open_answer_score=0.8, misconception_recurrence=0.1, retention_score=0.9, computed_mastery=0.86, last_reviewed_at=datetime.now(timezone.utc), next_review_date=date.today()),
            MasteryRecord(student_id=self.student.id, concept_id=weak.id, quiz_accuracy_score=0.4, open_answer_score=0.5, misconception_recurrence=0.6, retention_score=0.4, computed_mastery=0.42, last_reviewed_at=datetime.now(timezone.utc), next_review_date=date.today()),
            AttendanceRecord(org_id=self.org.id, classroom_id=1, student_id=self.student.id, attendance_date=date.today(), status="present", recorded_by=self.owner.id),
            QuizAttempt(student_id=self.student.id, concept_id=strong.id, question="Q", student_answer="A", is_correct=True, misconception_code=None, confidence=0.9, mode="quiz"),
            TeachBackAttempt(student_id=self.student.id, concept_id=weak.id, student_explanation="Because", clarity_score=0.7, accuracy_score=0.5, gpt_feedback="Gap"),
        ])
        self.db.commit()
        link_guardian(GuardianLinkRequest(parent_email="p@gv.test", student_id=self.student.id), current_user=self.owner, db=self.db)
        children = list_children(current_user=self.parent, db=self.db)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].name, "Child A")
        self.assertEqual(children[0].outstanding_cents, 5000)
        self.assertEqual(children[0].attendance["present"], 1)
        self.assertEqual(children[0].quiz_attempts, 1)
        self.assertEqual(children[0].quiz_correct, 1)
        self.assertEqual(children[0].teach_back_attempts, 1)
        self.assertEqual(children[0].strongest_topics[0].title, "Acids and Bases")
        self.assertEqual(children[0].weakest_topics[0].title, "Ionic Bonding")

    def test_parent_sees_only_linked_children(self) -> None:
        children = list_children(current_user=self.parent, db=self.db)
        self.assertEqual(children, [])

    def test_non_parent_blocked_from_children(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            list_children(current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    # ---- M11 ----

    def test_platform_admin_lists_orgs_and_usage(self) -> None:
        admin = User(org_id=None, email="root@slate.test", password_hash="x", role="platform_admin", name="Root")
        self.db.add(admin)
        self.db.commit()
        orgs = admin_list_orgs(current_user=admin, db=self.db)
        self.assertTrue(any(o.name == "Green Valley" for o in orgs))
        usage = admin_usage(current_user=admin, db=self.db)
        self.assertGreaterEqual(usage.orgs, 1)
        self.assertGreaterEqual(usage.school_orgs, 1)
        self.assertGreaterEqual(usage.active_users, 1)
        self.assertGreaterEqual(usage.outstanding_cents, 0)

    def test_non_admin_blocked_from_platform_endpoints(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            admin_list_orgs(current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
