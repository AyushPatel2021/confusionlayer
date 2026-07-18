from __future__ import annotations

import os
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
from app.models import Base, Student, User
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
        link_guardian(GuardianLinkRequest(parent_email="p@gv.test", student_id=self.student.id), current_user=self.owner, db=self.db)
        children = list_children(current_user=self.parent, db=self.db)
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].name, "Child A")
        self.assertEqual(children[0].outstanding_cents, 5000)

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

    def test_non_admin_blocked_from_platform_endpoints(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            admin_list_orgs(current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
