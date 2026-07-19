from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-org-billing-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import RegisterRequest, SignupRequest, create_user, register_org
from app.main import (
    ChangePlanRequest,
    ChangeRoleRequest,
    InvitationCreateRequest,
    change_member_role,
    change_subscription,
    connect_member_session,
    create_org_invitation,
    get_org,
    list_org_members,
    list_plans,
)
from app.models import Base, Plan, Student, Subscription, Teacher, User
from app.seed import backfill_tenancy


class OrgBillingTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        backfill_tenancy(self.db)  # seeds plans
        self.owner, self.org = register_org(
            self.db, RegisterRequest(org_name="Green Valley", segment="school", email="owner@gv.test", password="password123", name="Head")
        )

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_get_org_returns_plan_and_usage(self) -> None:
        response = get_org(current_user=self.owner, db=self.db)
        self.assertEqual(response.name, "Green Valley")
        self.assertIsNotNone(response.subscription)
        self.assertEqual(response.subscription.plan.segment, "school")
        self.assertGreaterEqual(response.usage.members, 1)

    def test_list_plans_scoped_to_segment(self) -> None:
        plans = list_plans(current_user=self.owner, db=self.db)
        self.assertTrue(plans)
        self.assertTrue(all(p.segment == "school" for p in plans))

    def test_change_plan_within_segment(self) -> None:
        # There's only one school plan seeded; changing to it should succeed and stay active.
        result = change_subscription(ChangePlanRequest(plan_code="school_free"), current_user=self.owner, db=self.db)
        self.assertEqual(result.status, "active")
        self.assertEqual(result.plan.code, "school_free")

    def test_change_plan_rejects_wrong_segment(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            change_subscription(ChangePlanRequest(plan_code="individual_free"), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_non_owner_cannot_change_plan(self) -> None:
        member = create_user(self.db, SignupRequest(email="t@gv.test", password="password123", role="teacher", name="T"))
        member.org_id = self.org.id
        self.db.commit()
        with self.assertRaises(HTTPException) as exc:
            change_subscription(ChangePlanRequest(plan_code="school_free"), current_user=member, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_change_member_role(self) -> None:
        member = create_user(self.db, SignupRequest(email="staff@gv.test", password="password123", role="student", name="Staff"))
        # simulate a non-profile-linked member (e.g. accountant invited) by making a parent
        parent = User(org_id=self.org.id, email="p@gv.test", password_hash="x", role="parent", name="P")
        self.db.add(parent)
        self.db.commit()
        updated = change_member_role(parent.id, ChangeRoleRequest(role="accountant"), current_user=self.owner, db=self.db)
        self.assertEqual(updated.role, "accountant")
        _ = member

    def test_members_and_pending_listed(self) -> None:
        create_org_invitation(InvitationCreateRequest(email="new@gv.test", role="teacher"), current_user=self.owner, db=self.db)
        response = list_org_members(current_user=self.owner, db=self.db)
        self.assertTrue(any(m.email == "owner@gv.test" for m in response.members))
        self.assertTrue(any(p.email == "new@gv.test" for p in response.pending))

    def test_institute_owner_can_manage_and_connect_members(self) -> None:
        institute_owner, institute = register_org(
            self.db,
            RegisterRequest(org_name="Slate Institute", segment="institute", email="owner@inst.test", password="password123", name="Institute Head"),
        )
        create_org_invitation(InvitationCreateRequest(email="teacher@inst.test", role="teacher"), current_user=institute_owner, db=self.db)
        response = list_org_members(current_user=institute_owner, db=self.db)
        self.assertTrue(any(m.email == "owner@inst.test" for m in response.members))
        self.assertTrue(any(p.email == "teacher@inst.test" for p in response.pending))

        teacher_profile = Teacher(name="Active Teacher")
        self.db.add(teacher_profile)
        self.db.flush()
        teacher = User(org_id=institute.id, email="active.teacher@inst.test", password_hash="x", role="teacher", name="Active Teacher", status="active", teacher_id=teacher_profile.id)
        self.db.add(teacher)
        self.db.commit()
        connected = connect_member_session(teacher.id, Response(), current_user=institute_owner, db=self.db)
        self.assertEqual(connected.user.email, "active.teacher@inst.test")
        self.assertEqual(connected.user.segment, "institute")

        with self.assertRaises(HTTPException) as exc:
            create_org_invitation(InvitationCreateRequest(email="admin@inst.test", role="school_admin"), current_user=institute_owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 422)

    def test_student_invite_blocked_over_plan_limit(self) -> None:
        # Set the org's plan student cap to 1, add one existing student, then a 2nd student invite must fail.
        subscription = self.db.scalar(select(Subscription).where(Subscription.org_id == self.org.id))
        plan = self.db.get(Plan, subscription.plan_id)
        plan.limits = {**plan.limits, "max_students": 1}
        profile = Student(name="Existing")
        self.db.add(profile)
        self.db.flush()
        self.db.add(User(org_id=self.org.id, email="s1@gv.test", password_hash="x", role="student", student_id=profile.id))
        self.db.commit()

        with self.assertRaises(HTTPException) as exc:
            create_org_invitation(InvitationCreateRequest(email="s2@gv.test", role="student"), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
