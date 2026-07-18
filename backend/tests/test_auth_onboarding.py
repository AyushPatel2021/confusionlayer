from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-onboarding-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException, Response
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import (
    ForgotPasswordRequest,
    InvitationAcceptRequest,
    InvitationCreateRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SignupRequest,
    create_user,
)
from app.main import (
    create_org_invitation,
    do_reset_password,
    forgot_password,
    invitation_accept,
    invitation_preview,
    login,
    me,
    register,
)
from app.models import Base, Organization, PasswordReset, Subscription, User
from app.seed import backfill_tenancy


class OnboardingTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        backfill_tenancy(self.db)  # seeds the 4 plans (register needs one)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def _register_owner(self, email="owner@school.test", segment="school", org="Green Valley"):
        return register(
            RegisterRequest(org_name=org, segment=segment, email=email, password="password123", name="Head"),
            response=Response(),
            db=self.db,
        )

    def test_register_creates_org_owner_and_free_subscription(self) -> None:
        resp = self._register_owner()

        self.assertEqual(resp.user.role, "owner")
        self.assertEqual(resp.user.org_name, "Green Valley")
        self.assertEqual(resp.user.segment, "school")
        org = self.db.scalar(select(Organization).where(Organization.name == "Green Valley"))
        self.assertIsNotNone(org)
        sub = self.db.scalar(select(Subscription).where(Subscription.org_id == org.id))
        self.assertIsNotNone(sub)
        self.assertEqual(sub.status, "active")

    def test_register_rejects_duplicate_email(self) -> None:
        self._register_owner(email="dup@school.test")
        with self.assertRaises(HTTPException) as exc:
            self._register_owner(email="dup@school.test", org="Another")
        self.assertEqual(exc.exception.status_code, 409)

    def test_login_after_register_and_me_returns_org(self) -> None:
        self._register_owner(email="login@school.test")
        resp = login(LoginRequest(email="login@school.test", password="password123"), response=Response(), db=self.db)
        self.assertEqual(resp.user.role, "owner")
        user = self.db.scalar(select(User).where(User.email == "login@school.test"))
        me_resp = me(current_user=user, db=self.db)
        self.assertEqual(me_resp.user.org_name, "Green Valley")

    def test_password_reset_flow(self) -> None:
        self._register_owner(email="reset@school.test")
        forgot_password(ForgotPasswordRequest(email="reset@school.test"), db=self.db)
        token = self.db.scalar(select(PasswordReset.token))
        self.assertIsNotNone(token)

        do_reset_password(ResetPasswordRequest(token=token, password="newpassword123"), db=self.db)
        # new password works, old fails
        login(LoginRequest(email="reset@school.test", password="newpassword123"), response=Response(), db=self.db)
        with self.assertRaises(HTTPException) as exc:
            login(LoginRequest(email="reset@school.test", password="password123"), response=Response(), db=self.db)
        self.assertEqual(exc.exception.status_code, 401)

    def test_reset_token_cannot_be_reused(self) -> None:
        self._register_owner(email="reuse@school.test")
        forgot_password(ForgotPasswordRequest(email="reuse@school.test"), db=self.db)
        token = self.db.scalar(select(PasswordReset.token))
        do_reset_password(ResetPasswordRequest(token=token, password="newpassword123"), db=self.db)
        with self.assertRaises(HTTPException) as exc:
            do_reset_password(ResetPasswordRequest(token=token, password="another123456"), db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_forgot_password_is_silent_for_unknown_email(self) -> None:
        forgot_password(ForgotPasswordRequest(email="nobody@nowhere.test"), db=self.db)
        self.assertEqual(self.db.scalar(select(func.count(PasswordReset.id))), 0)

    def test_invitation_create_preview_and_accept(self) -> None:
        self._register_owner(email="inviteowner@school.test")
        owner = self.db.scalar(select(User).where(User.email == "inviteowner@school.test"))
        result = create_org_invitation(
            InvitationCreateRequest(email="teacher@school.test", role="teacher", department="Teaching & learning"),
            current_user=owner,
            db=self.db,
        )
        token = result["token"]

        preview = invitation_preview(token=token, db=self.db)
        self.assertEqual(preview.email, "teacher@school.test")
        self.assertEqual(preview.role, "teacher")
        self.assertEqual(preview.department, "Teaching & learning")

        resp = invitation_accept(
            InvitationAcceptRequest(token=token, password="password123", name="New Teacher", profile={"phone": "9999999999"}),
            response=Response(),
            db=self.db,
        )
        self.assertEqual(resp.user.role, "teacher")
        self.assertEqual(resp.user.org_id, owner.org_id)
        new_user = self.db.scalar(select(User).where(User.email == "teacher@school.test"))
        self.assertIsNotNone(new_user.teacher_id)
        self.assertEqual(new_user.department, "Teaching & learning")
        self.assertEqual(new_user.profile_data["phone"], "9999999999")

        # token cannot be reused
        with self.assertRaises(HTTPException) as exc:
            invitation_accept(
                InvitationAcceptRequest(token=token, password="password123", name="Again"),
                response=Response(),
                db=self.db,
            )
        self.assertEqual(exc.exception.status_code, 404)

    def test_non_owner_cannot_invite(self) -> None:
        # a plain student user (created directly) cannot create invitations
        student = create_user(
            self.db, SignupRequest(email="s@school.test", password="password123", role="student", name="S")
        )
        with self.assertRaises(HTTPException) as exc:
            create_org_invitation(
                InvitationCreateRequest(email="x@school.test", role="teacher"),
                current_user=student,
                db=self.db,
            )
        self.assertEqual(exc.exception.status_code, 403)
