from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-learning-api-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import SignupRequest, create_user
from app.main import concept_detail, demo_context, student_syllabus, unlock_chapter
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
from sqlalchemy import func, select


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

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_demo_context_returns_user_classroom(self) -> None:
        response = demo_context(current_user=self.teacher_user, db=self.db)

        self.assertEqual(response.classroom.id, self.classroom.id)
        self.assertEqual(response.classroom.subject.name, "CBSE Class 10 Science")
        self.assertEqual(response.student_count, 1)

    def test_student_syllabus_respects_unlock_state(self) -> None:
        response = student_syllabus(current_user=self.student_user, db=self.db)

        self.assertEqual(response.chapters[0].locked, False)
        self.assertEqual(response.chapters[0].concepts[0].locked, False)
        self.assertEqual(response.chapters[1].locked, True)
        self.assertEqual(response.chapters[1].concepts[0].locked, True)

    def test_teacher_can_unlock_own_classroom_chapter(self) -> None:
        response = unlock_chapter(
            classroom_id=self.classroom.id,
            chapter_id=self.locked_chapter.id,
            current_user=self.teacher_user,
            db=self.db,
        )

        self.assertEqual(response.chapter_id, self.locked_chapter.id)

        student_response = student_syllabus(current_user=self.student_user, db=self.db)
        self.assertEqual(student_response.chapters[1].locked, False)

    def test_unlock_chapter_is_idempotent(self) -> None:
        first = unlock_chapter(
            classroom_id=self.classroom.id,
            chapter_id=self.locked_chapter.id,
            current_user=self.teacher_user,
            db=self.db,
        )
        second = unlock_chapter(
            classroom_id=self.classroom.id,
            chapter_id=self.locked_chapter.id,
            current_user=self.teacher_user,
            db=self.db,
        )
        unlock_count = self.db.scalar(
            select(func.count(ChapterUnlock.id)).where(
                ChapterUnlock.classroom_id == self.classroom.id,
                ChapterUnlock.chapter_id == self.locked_chapter.id,
            )
        )

        self.assertEqual(second.id, first.id)
        self.assertEqual(unlock_count, 1)

    def test_student_cannot_unlock_chapter(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            unlock_chapter(
                classroom_id=self.classroom.id,
                chapter_id=self.locked_chapter.id,
                current_user=self.student_user,
                db=self.db,
            )
        self.assertEqual(exc.exception.status_code, 403)

    def test_student_cannot_read_locked_concept_detail(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            concept_detail(concept_id=self.locked_concept.id, current_user=self.student_user, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_student_can_read_unlocked_concept_detail(self) -> None:
        response = concept_detail(concept_id=self.unlocked_concept.id, current_user=self.student_user, db=self.db)

        self.assertEqual(response.id, self.unlocked_concept.id)
        self.assertEqual(response.taxonomy[0].code, "BAL_SUBSCRIPT_CHANGE")

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
