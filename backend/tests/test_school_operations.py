from __future__ import annotations

import os
from datetime import date
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-school-operations")

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import RegisterRequest, register_org
from app.main import (
    AttendanceEntryRequest,
    AttendanceRequest,
    LibraryBookRequest,
    TimetableEntryRequest,
    TransportRouteRequest,
    create_library_book,
    create_timetable_entry,
    create_transport_route,
    delete_timetable_entry,
    global_search,
    list_attendance,
    list_library,
    list_timetable,
    list_transport_routes,
    save_attendance,
    student_report_card,
    update_org_settings,
    OrganizationSettingsRequest,
)
from app.models import Base, Classroom, ClassroomStudent, Student, Subject, Teacher, User
from app.seed import backfill_tenancy


class SchoolOperationsTest(TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db: Session = sessionmaker(bind=engine)()
        backfill_tenancy(self.db)
        self.owner, self.org = register_org(self.db, RegisterRequest(org_name="Green Valley", segment="school", email="owner@gv.test", password="password123", name="Head"))
        teacher = Teacher(name="Teacher")
        student = Student(name="Asha")
        subject = Subject(org_id=self.org.id, name="Science", board="CBSE", class_level="10")
        self.db.add_all([teacher, student, subject]); self.db.flush()
        self.db.add(User(org_id=self.org.id, email="asha@gv.test", name="Asha", password_hash="x", role="student", student_id=student.id))
        self.classroom = Classroom(org_id=self.org.id, teacher_id=teacher.id, subject_id=subject.id, name="10A Science")
        self.db.add(self.classroom); self.db.flush()
        self.db.add(ClassroomStudent(classroom_id=self.classroom.id, student_id=student.id)); self.db.commit()
        self.student = student

    def tearDown(self) -> None:
        self.db.close()

    def test_attendance_and_report_card_are_org_scoped(self) -> None:
        result = save_attendance(self.classroom.id, AttendanceRequest(attendance_date=date.today(), entries=[AttendanceEntryRequest(student_id=self.student.id, status="present")]), current_user=self.owner, db=self.db)
        self.assertEqual(result["saved"], 1)
        attendance = list_attendance(self.classroom.id, attendance_date=date.today(), current_user=self.owner, db=self.db)
        self.assertEqual(attendance["students"][0]["status"], "present")
        report = student_report_card(self.student.id, current_user=self.owner, db=self.db)
        self.assertEqual(report["attendance"]["present"], 1)

    def test_school_operations_and_search(self) -> None:
        timetable_entry = create_timetable_entry(TimetableEntryRequest(classroom_id=self.classroom.id, weekday=0, starts_at="09:00", ends_at="10:00"), current_user=self.owner, db=self.db)
        create_library_book(LibraryBookRequest(title="The Science Book", copies_total=2), current_user=self.owner, db=self.db)
        create_transport_route(TransportRouteRequest(name="North Route", stops=["Park"]), current_user=self.owner, db=self.db)
        self.assertEqual(len(list_timetable(current_user=self.owner, db=self.db)), 1)
        delete_timetable_entry(timetable_entry["id"], current_user=self.owner, db=self.db)
        self.assertEqual(len(list_timetable(current_user=self.owner, db=self.db)), 0)
        self.assertEqual(len(list_library(current_user=self.owner, db=self.db)), 1)
        self.assertEqual(len(list_transport_routes(current_user=self.owner, db=self.db)), 1)
        self.assertIn("Student", [item["kind"] for item in global_search("Asha", current_user=self.owner, db=self.db)["results"]])

    def test_owner_can_update_workspace_preferences(self) -> None:
        updated = update_org_settings(OrganizationSettingsRequest(name="Green Valley School", timezone="Asia/Kolkata", currency="INR"), current_user=self.owner, db=self.db)
        self.assertEqual(updated["name"], "Green Valley School")
