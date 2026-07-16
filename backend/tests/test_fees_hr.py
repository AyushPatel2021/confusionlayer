from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-fees-hr-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import RegisterRequest, register_org
from app.main import (
    EmployeeCreateRequest,
    FeeStructureCreateRequest,
    InvoiceCreateRequest,
    PaymentCreateRequest,
    PayrollRunCreateRequest,
    create_employee,
    create_fee_structure,
    create_invoice,
    create_payroll_run,
    fees_summary,
    list_invoices,
    record_payment,
    void_invoice,
)
from app.models import Base
from app.seed import backfill_tenancy


class FeesHrTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        backfill_tenancy(self.db)
        self.owner, self.org = register_org(
            self.db, RegisterRequest(org_name="Green Valley", segment="school", email="o@gv.test", password="password123", name="Head")
        )
        self.inst_owner, _ = register_org(
            self.db, RegisterRequest(org_name="Coaching", segment="institute", email="o@ci.test", password="password123", name="B")
        )

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    # ---- Fees ----

    def test_invoice_payment_status_progression(self) -> None:
        inv = create_invoice(InvoiceCreateRequest(recipient_name="Asha", amount_cents=10000), current_user=self.owner, db=self.db)
        self.assertEqual(inv.status, "unpaid")
        after_partial = record_payment(inv.id, PaymentCreateRequest(amount_cents=4000), current_user=self.owner, db=self.db)
        self.assertEqual(after_partial.status, "partial")
        self.assertEqual(after_partial.paid_cents, 4000)
        after_full = record_payment(inv.id, PaymentCreateRequest(amount_cents=6000), current_user=self.owner, db=self.db)
        self.assertEqual(after_full.status, "paid")

    def test_void_blocks_payment(self) -> None:
        inv = create_invoice(InvoiceCreateRequest(recipient_name="X", amount_cents=5000), current_user=self.owner, db=self.db)
        voided = void_invoice(inv.id, current_user=self.owner, db=self.db)
        self.assertEqual(voided.status, "void")
        with self.assertRaises(HTTPException) as exc:
            record_payment(inv.id, PaymentCreateRequest(amount_cents=100), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_fees_summary(self) -> None:
        a = create_invoice(InvoiceCreateRequest(recipient_name="A", amount_cents=10000), current_user=self.owner, db=self.db)
        create_invoice(InvoiceCreateRequest(recipient_name="B", amount_cents=5000), current_user=self.owner, db=self.db)
        record_payment(a.id, PaymentCreateRequest(amount_cents=10000), current_user=self.owner, db=self.db)
        summary = fees_summary(current_user=self.owner, db=self.db)
        self.assertEqual(summary.billed_cents, 15000)
        self.assertEqual(summary.collected_cents, 10000)
        self.assertEqual(summary.outstanding_cents, 5000)

    def test_fee_structure_and_module_gate(self) -> None:
        create_fee_structure(FeeStructureCreateRequest(name="Term 1", amount_cents=20000), current_user=self.owner, db=self.db)
        self.assertEqual(len(list_invoices(current_user=self.owner, db=self.db)), 0)
        with self.assertRaises(HTTPException) as exc:  # institute plan lacks accounting
            create_invoice(InvoiceCreateRequest(recipient_name="x", amount_cents=1), current_user=self.inst_owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    # ---- HR / payroll ----

    def test_payroll_run_generates_payslips(self) -> None:
        create_employee(EmployeeCreateRequest(name="Teacher A", salary_cents=300000), current_user=self.owner, db=self.db)
        create_employee(EmployeeCreateRequest(name="Teacher B", salary_cents=250000), current_user=self.owner, db=self.db)
        run = create_payroll_run(PayrollRunCreateRequest(period="2026-07"), current_user=self.owner, db=self.db)
        self.assertEqual(run.status, "finalized")
        self.assertEqual(len(run.payslips), 2)
        self.assertEqual(sum(s.net_cents for s in run.payslips), 550000)

    def test_payroll_requires_employees(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_payroll_run(PayrollRunCreateRequest(period="2026-07"), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_hr_module_gated_for_institute(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_employee(EmployeeCreateRequest(name="X", salary_cents=1), current_user=self.inst_owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
