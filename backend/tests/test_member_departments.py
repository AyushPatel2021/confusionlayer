from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-member-departments")

from fastapi import HTTPException, Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import InvitationAcceptRequest, InvitationCreateRequest, RegisterRequest, register_org
from app.main import (
    ChangeMemberDepartmentRequest,
    change_member_department,
    create_org_invitation,
    invitation_accept,
    remove_member,
)
from app.models import Base, User
from app.seed import backfill_tenancy


class MemberDepartmentTest(TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db: Session = sessionmaker(bind=engine)()
        backfill_tenancy(self.db)
        self.owner, _ = register_org(self.db, RegisterRequest(org_name="Green Valley", segment="school", email="owner@gv.test", password="password123", name="Head"))

    def tearDown(self) -> None:
        self.db.close()

    def test_department_is_persisted_and_member_removal_is_safe(self) -> None:
        invitation = create_org_invitation(InvitationCreateRequest(email="accounts@gv.test", role="accountant", department="Accounts"), current_user=self.owner, db=self.db)
        invitation_accept(InvitationAcceptRequest(token=invitation["token"], password="password123", name="Asha"), response=Response(), db=self.db)
        member = self.db.scalar(select(User).where(User.email == "accounts@gv.test"))
        updated = change_member_department(member.id, ChangeMemberDepartmentRequest(department="Front-office"), current_user=self.owner, db=self.db)
        self.assertEqual(updated.department, "Front-office")
        removed = remove_member(member.id, current_user=self.owner, db=self.db)
        self.assertEqual(removed.status, "inactive")

    def test_invalid_department_is_rejected(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_org_invitation(InvitationCreateRequest(email="bad@gv.test", role="teacher", department="Unknown"), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 422)
