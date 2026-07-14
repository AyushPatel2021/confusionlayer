from __future__ import annotations

import os
from collections.abc import Generator
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-learning-api-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import SignupRequest, create_access_token, create_user
from app.db import get_db
from app.main import app
from app.models import (
    Base,
    Chapter,
    ChapterUnlock,
    Classroom,
    ClassroomStudent,
    Concept,
    MisconceptionTaxonomy,
    Student,
    Subject,
    Teacher,
)


class LearningApiTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db: Session = self.session_factory()
        self._seed_minimal_classroom()

        def override_db() -> Generator[Session, None, None]:
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.db.close()
        self.engine.dispose()

    def test_demo_context_returns_user_classroom(self) -> None:
        token = self._token_for(self.teacher_user)

        response = self.client.get("/api/demo/context", headers=self._auth(token))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["classroom"]["id"], self.classroom.id)
        self.assertEqual(body["classroom"]["subject"]["name"], "CBSE Class 10 Science")
        self.assertEqual(body["student_count"], 1)

    def test_student_syllabus_respects_unlock_state(self) -> None:
        token = self._token_for(self.student_user)

        response = self.client.get("/api/student/syllabus", headers=self._auth(token))

        self.assertEqual(response.status_code, 200)
        chapters = response.json()["chapters"]
        self.assertEqual(chapters[0]["locked"], False)
        self.assertEqual(chapters[0]["concepts"][0]["locked"], False)
        self.assertEqual(chapters[1]["locked"], True)
        self.assertEqual(chapters[1]["concepts"][0]["locked"], True)

    def test_teacher_can_unlock_own_classroom_chapter(self) -> None:
        token = self._token_for(self.teacher_user)

        response = self.client.post(
            f"/api/teacher/classrooms/{self.classroom.id}/chapters/{self.locked_chapter.id}/unlock",
            headers=self._auth(token),
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["chapter_id"], self.locked_chapter.id)

        student_response = self.client.get("/api/student/syllabus", headers=self._auth(self._token_for(self.student_user)))
        self.assertEqual(student_response.json()["chapters"][1]["locked"], False)

    def test_student_cannot_unlock_chapter(self) -> None:
        token = self._token_for(self.student_user)

        response = self.client.post(
            f"/api/teacher/classrooms/{self.classroom.id}/chapters/{self.locked_chapter.id}/unlock",
            headers=self._auth(token),
        )

        self.assertEqual(response.status_code, 403)

    def test_student_cannot_read_locked_concept_detail(self) -> None:
        token = self._token_for(self.student_user)

        response = self.client.get(f"/api/concepts/{self.locked_concept.id}", headers=self._auth(token))

        self.assertEqual(response.status_code, 403)

    def test_student_can_read_unlocked_concept_detail(self) -> None:
        token = self._token_for(self.student_user)

        response = self.client.get(f"/api/concepts/{self.unlocked_concept.id}", headers=self._auth(token))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id"], self.unlocked_concept.id)
        self.assertEqual(body["taxonomy"][0]["code"], "BAL_SUBSCRIPT_CHANGE")

    def _seed_minimal_classroom(self) -> None:
        subject = Subject(name="CBSE Class 10 Science", board="CBSE", class_level="10")
        teacher = Teacher(name="Teacher One")
        student = Student(name="Student One")
        self.db.add_all([subject, teacher, student])
        self.db.flush()

        classroom = Classroom(name="Class 10A", teacher_id=teacher.id, subject_id=subject.id)
        self.db.add(classroom)
        self.db.flush()
        self.db.add(ClassroomStudent(classroom_id=classroom.id, student_id=student.id))

        unlocked_chapter = Chapter(subject_id=subject.id, title="Chemical Reactions", order=1)
        locked_chapter = Chapter(subject_id=subject.id, title="Metals and Non-metals", order=2)
        self.db.add_all([unlocked_chapter, locked_chapter])
        self.db.flush()

        unlocked_concept = Concept(chapter_id=unlocked_chapter.id, title="Balancing Chemical Equations", order=1)
        locked_concept = Concept(chapter_id=locked_chapter.id, title="Reactivity Series", order=1)
        self.db.add_all([unlocked_concept, locked_concept])
        self.db.flush()
        self.db.add(
            MisconceptionTaxonomy(
                concept_id=unlocked_concept.id,
                code="BAL_SUBSCRIPT_CHANGE",
                description="Changes subscripts instead of coefficients.",
            )
        )
        self.db.add(ChapterUnlock(classroom_id=classroom.id, chapter_id=unlocked_chapter.id, unlocked_by=teacher.id))
        self.db.commit()

        self.subject = subject
        self.teacher = teacher
        self.student = student
        self.classroom = classroom
        self.unlocked_chapter = unlocked_chapter
        self.locked_chapter = locked_chapter
        self.unlocked_concept = unlocked_concept
        self.locked_concept = locked_concept
        self.teacher_user = create_user(
            self.db,
            SignupRequest(email="teacher@example.com", password="password123", role="teacher", name="Teacher Login"),
        )
        self.teacher_user.teacher_id = teacher.id
        self.student_user = create_user(
            self.db,
            SignupRequest(email="student@example.com", password="password123", role="student", name="Student Login"),
        )
        self.student_user.student_id = student.id
        self.db.commit()

    @staticmethod
    def _token_for(user) -> str:
        return create_access_token(user)

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
