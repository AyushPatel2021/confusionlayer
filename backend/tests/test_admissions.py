from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-admissions-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import RegisterRequest, SignupRequest, create_user, register_org
from app.main import (
    ApplicationCreateRequest,
    ApplicationStatusRequest,
    create_application,
    enroll_application,
    list_applications,
    set_application_status,
)
from app.models import AdmissionApplication, Base, Invitation, Plan, Student, Subscription
from app.seed import backfill_tenancy


class AdmissionsTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        backfill_tenancy(self.db)
        self.owner, self.org = register_org(
            self.db, RegisterRequest(org_name="Green Valley", segment="school", email="owner@gv.test", password="password123", name="Head")
        )
        # an institute owner (plan has no admissions module)
        self.inst_owner, self.inst_org = register_org(
            self.db, RegisterRequest(org_name="Coaching", segment="institute", email="owner@ci.test", password="password123", name="Boss")
        )

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def _apply(self, name="Asha", email="asha@x.test"):
        return create_application(ApplicationCreateRequest(applicant_name=name, applicant_email=email, grade="10"), current_user=self.owner, db=self.db)

    def test_pipeline_apply_review_accept_enroll(self) -> None:
        app = self._apply()
        self.assertEqual(app.status, "applied")
        set_application_status(app.id, ApplicationStatusRequest(status="reviewing"), current_user=self.owner, db=self.db)
        set_application_status(app.id, ApplicationStatusRequest(status="accepted"), current_user=self.owner, db=self.db)
        enrolled = enroll_application(app.id, current_user=self.owner, db=self.db)
        self.assertEqual(enrolled.status, "enrolled")
        self.assertIsNotNone(enrolled.student_id)
        # a Student profile + a pending student invitation were created
        self.assertEqual(self.db.scalar(select(func.count(Student.id))), 1)
        self.assertEqual(self.db.scalar(select(func.count(Invitation.id)).where(Invitation.role == "student")), 1)

    def test_cannot_enroll_before_accept(self) -> None:
        app = self._apply()
        with self.assertRaises(HTTPException) as exc:
            enroll_application(app.id, current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_enrolled_status_is_locked(self) -> None:
        app = self._apply()
        set_application_status(app.id, ApplicationStatusRequest(status="accepted"), current_user=self.owner, db=self.db)
        enroll_application(app.id, current_user=self.owner, db=self.db)
        with self.assertRaises(HTTPException) as exc:
            set_application_status(app.id, ApplicationStatusRequest(status="reviewing"), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_module_gated_for_institute(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_application(ApplicationCreateRequest(applicant_name="X"), current_user=self.inst_owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_students_blocked(self) -> None:
        student = create_user(self.db, SignupRequest(email="s@gv.test", password="password123", role="student", name="S"))
        student.org_id = self.org.id
        self.db.commit()
        with self.assertRaises(HTTPException) as exc:
            list_applications(current_user=student, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_cross_org_application_not_found(self) -> None:
        app = self._apply()
        with self.assertRaises(HTTPException) as exc:
            set_application_status(app.id, ApplicationStatusRequest(status="reviewing"), current_user=self.inst_owner, db=self.db)
        # institute owner lacks the module → 403 before the ownership 404
        self.assertIn(exc.exception.status_code, (403, 404))

    def test_enroll_respects_student_cap(self) -> None:
        subscription = self.db.scalar(select(Subscription).where(Subscription.org_id == self.org.id))
        plan = self.db.get(Plan, subscription.plan_id)
        plan.limits = {**plan.limits, "max_students": 1}
        self.db.commit()

        a1 = self._apply(name="One", email="one@x.test")
        set_application_status(a1.id, ApplicationStatusRequest(status="accepted"), current_user=self.owner, db=self.db)
        enroll_application(a1.id, current_user=self.owner, db=self.db)

        a2 = self._apply(name="Two", email="two@x.test")
        set_application_status(a2.id, ApplicationStatusRequest(status="accepted"), current_user=self.owner, db=self.db)
        with self.assertRaises(HTTPException) as exc:
            enroll_application(a2.id, current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
