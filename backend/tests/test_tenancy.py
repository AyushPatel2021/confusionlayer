from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-tenancy-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import SignupRequest, create_user
from app.main import confusion_brief, demo_context, unlock_chapter
from app.models import (
    Base,
    Chapter,
    Classroom,
    ClassroomStudent,
    Concept,
    Organization,
    Plan,
    Subject,
    Subscription,
    Teacher,
)
from app.seed import backfill_tenancy


class TenancyIsolationTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        self._seed_two_orgs()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_teacher_cannot_view_other_orgs_confusion_brief(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            confusion_brief(classroom_id=self.classroom_b.id, current_user=self.teacher_a, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
        self.assertIn("another organization", exc.exception.detail)

    def test_teacher_cannot_unlock_other_orgs_chapter(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            unlock_chapter(
                classroom_id=self.classroom_b.id,
                chapter_id=self.chapter.id,
                current_user=self.teacher_a,
                db=self.db,
            )
        self.assertEqual(exc.exception.status_code, 403)

    def test_teacher_can_view_own_orgs_confusion_brief(self) -> None:
        response = confusion_brief(classroom_id=self.classroom_a.id, current_user=self.teacher_a, db=self.db)
        self.assertEqual(response.classroom_id, self.classroom_a.id)

    def test_demo_context_resolves_users_own_org_classroom(self) -> None:
        response = demo_context(current_user=self.teacher_a, db=self.db)
        self.assertEqual(response.classroom.id, self.classroom_a.id)

    def _seed_two_orgs(self) -> None:
        subject = Subject(name="CBSE Class 10 Science", board="CBSE", class_level="10")
        self.db.add(subject)
        self.db.flush()
        chapter = Chapter(subject_id=subject.id, title="Chemical Reactions", order=1)
        self.db.add(chapter)
        self.db.flush()
        self.db.add(Concept(chapter_id=chapter.id, title="Balancing Chemical Equations", order=1))

        org_a = Organization(name="Org A", slug="org-a", segment="school")
        org_b = Organization(name="Org B", slug="org-b", segment="school")
        teacher_a = Teacher(name="Teacher A")
        teacher_b = Teacher(name="Teacher B")
        self.db.add_all([org_a, org_b, teacher_a, teacher_b])
        self.db.flush()

        classroom_a = Classroom(name="A-10", org_id=org_a.id, teacher_id=teacher_a.id, subject_id=subject.id)
        classroom_b = Classroom(name="B-10", org_id=org_b.id, teacher_id=teacher_b.id, subject_id=subject.id)
        self.db.add_all([classroom_a, classroom_b])
        self.db.flush()
        self.db.commit()

        self.subject = subject
        self.chapter = chapter
        self.classroom_a = classroom_a
        self.classroom_b = classroom_b

        self.teacher_a = create_user(
            self.db, SignupRequest(email="a@example.com", password="password123", role="teacher", name="A")
        )
        self.teacher_a.teacher_id = teacher_a.id
        self.teacher_a.org_id = org_a.id
        self.db.commit()


class TenancyBackfillTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_backfill_creates_plans_org_subscription_and_attaches(self) -> None:
        subject = Subject(name="S", board="CBSE", class_level="10")
        teacher = Teacher(name="T")
        self.db.add_all([subject, teacher])
        self.db.flush()
        classroom = Classroom(name="C", teacher_id=teacher.id, subject_id=subject.id)  # no org_id
        self.db.add(classroom)
        self.db.commit()

        result = backfill_tenancy(self.db)

        self.assertEqual(self.db.scalar(select(func.count(Plan.id))), 4)
        org = self.db.scalar(select(Organization).where(Organization.slug == "confusionlayer-demo"))
        self.assertIsNotNone(org)
        self.assertEqual(self.db.scalar(select(func.count(Subscription.id)).where(Subscription.org_id == org.id)), 1)
        self.db.refresh(classroom)
        self.assertEqual(classroom.org_id, org.id)
        self.assertEqual(result["classrooms"], 1)

    def test_backfill_is_idempotent(self) -> None:
        backfill_tenancy(self.db)
        backfill_tenancy(self.db)
        self.assertEqual(self.db.scalar(select(func.count(Plan.id))), 4)
        self.assertEqual(self.db.scalar(select(func.count(Organization.id))), 1)
        self.assertEqual(self.db.scalar(select(func.count(Subscription.id))), 1)
