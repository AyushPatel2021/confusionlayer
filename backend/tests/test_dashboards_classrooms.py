from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-dashboard-classroom-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import RegisterRequest, SignupRequest, create_user, register_org
from app.main import (
    ClassroomCreateRequest,
    ClassroomEnrollmentRequest,
    ClassroomUpdateRequest,
    classroom_options,
    create_classroom,
    delete_classroom,
    dashboard,
    enroll_classroom_student,
    list_classrooms,
    remove_classroom_student,
    update_classroom,
)
from app.models import Base, Subject
from app.seed import backfill_tenancy


class DashboardClassroomTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        backfill_tenancy(self.db)
        self.owner, self.org = register_org(self.db, RegisterRequest(org_name="Green Valley", segment="school", email="owner@gv.test", password="password123", name="Head"))
        self.teacher = create_user(self.db, SignupRequest(email="teacher@gv.test", password="password123", role="teacher", name="Teacher One"))
        self.teacher.org_id = self.org.id
        self.student = create_user(self.db, SignupRequest(email="student@gv.test", password="password123", role="student", name="Student One"))
        self.student.org_id = self.org.id
        self.subject = Subject(name="Science", board="CBSE", class_level="10", org_id=self.org.id)
        self.db.add(self.subject)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_owner_creates_classroom_enrols_and_removes_student(self) -> None:
        classroom = create_classroom(ClassroomCreateRequest(name="10 A", subject_id=self.subject.id, teacher_id=self.teacher.teacher_id), current_user=self.owner, db=self.db)
        self.assertEqual(classroom.teacher.name, "Teacher One")

        enrolled = enroll_classroom_student(classroom.id, ClassroomEnrollmentRequest(student_id=self.student.student_id), current_user=self.owner, db=self.db)
        self.assertEqual([student.name for student in enrolled.students], ["Student One"])

        remove_classroom_student(classroom.id, self.student.student_id, current_user=self.owner, db=self.db)
        self.assertEqual(list_classrooms(current_user=self.owner, db=self.db)[0].students, [])

    def test_options_and_dashboard_are_org_scoped(self) -> None:
        options = classroom_options(current_user=self.owner, db=self.db)
        self.assertEqual([subject.name for subject in options.subjects], ["Science"])
        self.assertEqual([teacher.name for teacher in options.teachers], ["Teacher One"])
        self.assertEqual([student.name for student in options.students], ["Student One"])

        response = dashboard(current_user=self.owner, db=self.db)
        self.assertEqual(response.title, "School overview")
        self.assertTrue(response.chart.labels)

    def test_teacher_cannot_manage_classrooms(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            list_classrooms(current_user=self.teacher, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_owner_edits_and_deletes_classroom(self) -> None:
        classroom = create_classroom(ClassroomCreateRequest(name="10 A", subject_id=self.subject.id, teacher_id=self.teacher.teacher_id), current_user=self.owner, db=self.db)
        updated = update_classroom(classroom.id, ClassroomUpdateRequest(name="10 B", subject_id=self.subject.id, teacher_id=self.teacher.teacher_id), current_user=self.owner, db=self.db)
        self.assertEqual(updated.name, "10 B")
        delete_classroom(classroom.id, current_user=self.owner, db=self.db)
        self.assertEqual(list_classrooms(current_user=self.owner, db=self.db), [])
