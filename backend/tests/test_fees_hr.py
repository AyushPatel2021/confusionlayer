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
    EmployeeStatusRequest,
    FeeStructureCreateRequest,
    FeeStructureApplyRequest,
    InvoiceCreateRequest,
    InvoiceLineItemRequest,
    PaymentCreateRequest,
    PayrollRunCreateRequest,
    create_employee,
    set_employee_status,
    create_fee_structure,
    delete_fee_structure,
    apply_fee_structure,
    create_invoice,
    create_payroll_run,
    fee_student_options,
    fees_summary,
    list_invoices,
    update_fee_structure,
    record_payment,
    void_invoice,
)
from app.models import Base, Student, User
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

    def test_invoice_line_items_are_persisted_and_totalled(self) -> None:
        invoice = create_invoice(
            InvoiceCreateRequest(
                recipient_name="Asha",
                amount_cents=12500,
                line_items=[
                    InvoiceLineItemRequest(description="Tuition", amount_cents=10000),
                    InvoiceLineItemRequest(description="Lab fee", amount_cents=2500),
                ],
            ),
            current_user=self.owner,
            db=self.db,
        )
        self.assertEqual([(item.description, item.amount_cents) for item in invoice.line_items], [("Tuition", 10000), ("Lab fee", 2500)])
        with self.assertRaises(HTTPException) as exc:
            create_invoice(
                InvoiceCreateRequest(recipient_name="Asha", amount_cents=10000, line_items=[InvoiceLineItemRequest(description="Tuition", amount_cents=9000)]),
                current_user=self.owner,
                db=self.db,
            )
        self.assertEqual(exc.exception.status_code, 422)

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
        structure = create_fee_structure(FeeStructureCreateRequest(name="Term 1", amount_cents=20000), current_user=self.owner, db=self.db)
        updated = update_fee_structure(structure.id, FeeStructureCreateRequest(name="Term 1 revised", amount_cents=25000), current_user=self.owner, db=self.db)
        self.assertEqual((updated.name, updated.amount_cents), ("Term 1 revised", 25000))
        delete_fee_structure(structure.id, current_user=self.owner, db=self.db)
        self.assertEqual(len(list_invoices(current_user=self.owner, db=self.db)), 0)
        with self.assertRaises(HTTPException) as exc:  # institute plan lacks accounting
            create_invoice(InvoiceCreateRequest(recipient_name="x", amount_cents=1), current_user=self.inst_owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_apply_fee_structure_creates_one_invoice_per_student(self) -> None:
        students = [Student(name="Asha"), Student(name="Ravi")]
        self.db.add_all(students)
        self.db.flush()
        self.db.add_all([
            User(org_id=self.org.id, email="asha.apply@gv.test", password_hash="x", role="student", name="Asha", student_id=students[0].id),
            User(org_id=self.org.id, email="ravi.apply@gv.test", password_hash="x", role="student", name="Ravi", student_id=students[1].id),
        ])
        self.db.commit()
        structure = create_fee_structure(FeeStructureCreateRequest(name="Term 1 tuition", amount_cents=20000), current_user=self.owner, db=self.db)
        invoices = apply_fee_structure(structure.id, FeeStructureApplyRequest(student_ids=[students[0].id, students[1].id]), current_user=self.owner, db=self.db)
        self.assertEqual([(invoice.recipient_name, invoice.amount_cents) for invoice in invoices], [("Asha", 20000), ("Ravi", 20000)])
        self.assertTrue(all(invoice.line_items[0].description == "Term 1 tuition" for invoice in invoices))

    def test_invoice_student_link_requires_org_membership(self) -> None:
        student = Student(name="Asha")
        self.db.add(student)
        self.db.flush()
        member = User(org_id=self.org.id, email="asha@gv.test", password_hash="x", role="student", name="Asha", student_id=student.id)
        self.db.add(member)
        self.db.commit()

        options = fee_student_options(current_user=self.owner, db=self.db)
        self.assertEqual([(item.id, item.name) for item in options], [(student.id, "Asha")])
        invoice = create_invoice(InvoiceCreateRequest(recipient_name="Asha", student_id=student.id, amount_cents=1000), current_user=self.owner, db=self.db)
        self.assertEqual(invoice.student_id, student.id)

        outsider = Student(name="Outside")
        self.db.add(outsider)
        self.db.commit()
        with self.assertRaises(HTTPException) as exc:
            create_invoice(InvoiceCreateRequest(recipient_name="Outside", student_id=outsider.id, amount_cents=1000), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 404)

    # ---- HR / payroll ----

    def test_payroll_run_generates_payslips(self) -> None:
        create_employee(EmployeeCreateRequest(name="Teacher A", salary_cents=300000), current_user=self.owner, db=self.db)
        create_employee(EmployeeCreateRequest(name="Teacher B", salary_cents=250000), current_user=self.owner, db=self.db)
        run = create_payroll_run(PayrollRunCreateRequest(period="2026-07"), current_user=self.owner, db=self.db)
        self.assertEqual(run.status, "finalized")
        self.assertEqual(len(run.payslips), 2)
        self.assertEqual(sum(s.net_cents for s in run.payslips), 550000)

    def test_employee_can_be_deactivated_without_losing_profile(self) -> None:
        employee = create_employee(EmployeeCreateRequest(name="Teacher A", phone="9876543210", join_date="2026-06-01", salary_cents=300000), current_user=self.owner, db=self.db)
        inactive = set_employee_status(employee.id, EmployeeStatusRequest(status="inactive"), current_user=self.owner, db=self.db)
        self.assertEqual((inactive.status, inactive.phone, str(inactive.join_date)), ("inactive", "9876543210", "2026-06-01"))

    def test_payroll_requires_employees(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_payroll_run(PayrollRunCreateRequest(period="2026-07"), current_user=self.owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 400)

    def test_hr_module_gated_for_institute(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_employee(EmployeeCreateRequest(name="X", salary_cents=1), current_user=self.inst_owner, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)
