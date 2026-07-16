from __future__ import annotations

import os
from datetime import UTC, date, datetime
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-selfstart-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai import TutorialContent
from app.auth import SignupRequest, create_user
from app.main import SelfStartRequest, self_start_tutorial, student_progress
from app.models import (
    Base,
    Chapter,
    Classroom,
    ClassroomStudent,
    Concept,
    MasteryHistory,
    MasteryRecord,
    Student,
    Subject,
    Teacher,
)


class SelfStartProgressTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db: Session = self.session_factory()
        self._seed()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    # ---- Self-start ------------------------------------------------------

    def test_self_start_generates_for_student_without_unlock(self) -> None:
        with patch(
            "app.main.generate_self_start_tutorial",
            return_value=TutorialContent("Explanation of black holes.", "Like a vacuum.", "Worked example.", ""),
        ) as generate:
            response = self_start_tutorial(
                payload=SelfStartRequest(topic="Black holes", reading_level="Class 10"),
                current_user=self.student_user,
                db=self.db,
            )

        self.assertEqual(response.explanation, "Explanation of black holes.")
        generate.assert_called_once()
        # the free-form topic is passed through to the generator
        self.assertIn("Black holes", generate.call_args.args)

    def test_self_start_rejects_empty_topic_before_ai_call(self) -> None:
        with patch("app.main.generate_self_start_tutorial") as generate:
            with self.assertRaises(HTTPException) as exc:
                self_start_tutorial(
                    payload=SelfStartRequest(topic="   ", reading_level="Class 10"),
                    current_user=self.student_user,
                    db=self.db,
                )
        self.assertEqual(exc.exception.status_code, 400)
        generate.assert_not_called()

    def test_self_start_blocks_teachers(self) -> None:
        with patch("app.main.generate_self_start_tutorial") as generate:
            with self.assertRaises(HTTPException) as exc:
                self_start_tutorial(
                    payload=SelfStartRequest(topic="Black holes"),
                    current_user=self.teacher_user,
                    db=self.db,
                )
        self.assertEqual(exc.exception.status_code, 403)
        generate.assert_not_called()

    # ---- Progress --------------------------------------------------------

    def test_progress_returns_history_series_and_summary(self) -> None:
        response = student_progress(current_user=self.student_user, db=self.db)

        self.assertEqual(response.student_name, "Student One")
        self.assertEqual(response.mastered_threshold, 0.8)
        self.assertEqual(response.summary.concept_count, 1)
        concept = response.concepts[0]
        self.assertEqual(concept.concept_id, self.concept.id)
        self.assertEqual(len(concept.history), 3)
        # history is returned in chronological order
        self.assertEqual(
            [point.recorded_at for point in concept.history],
            sorted(point.recorded_at for point in concept.history),
        )
        self.assertGreaterEqual(concept.effective_mastery, 0.0)
        self.assertLessEqual(concept.effective_mastery, concept.current_mastery)

    def test_progress_blocks_teachers(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            student_progress(current_user=self.teacher_user, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    # ---- Seed ------------------------------------------------------------

    def _seed(self) -> None:
        subject = Subject(name="CBSE Class 10 Science", board="CBSE", class_level="10")
        teacher = Teacher(name="Teacher One")
        student = Student(name="Student One")
        self.db.add_all([subject, teacher, student])
        self.db.flush()

        classroom = Classroom(name="Class 10A", teacher_id=teacher.id, subject_id=subject.id)
        self.db.add(classroom)
        self.db.flush()
        self.db.add(ClassroomStudent(classroom_id=classroom.id, student_id=student.id))

        chapter = Chapter(subject_id=subject.id, title="Chemical Reactions", order=1)
        self.db.add(chapter)
        self.db.flush()
        concept = Concept(chapter_id=chapter.id, title="Balancing Chemical Equations", order=1)
        self.db.add(concept)
        self.db.flush()

        self.db.add(
            MasteryRecord(
                student_id=student.id,
                concept_id=concept.id,
                quiz_accuracy_score=0.7,
                open_answer_score=0.6,
                misconception_recurrence=0.2,
                retention_score=0.8,
                computed_mastery=0.68,
                last_reviewed_at=datetime(2026, 7, 8, tzinfo=UTC),
                next_review_date=date(2026, 7, 22),
            )
        )
        for offset, value in ((21, 0.4), (14, 0.55), (7, 0.68)):
            self.db.add(
                MasteryHistory(
                    student_id=student.id,
                    concept_id=concept.id,
                    mastery=value,
                    recorded_at=date(2026, 6, 24) if offset == 21 else (date(2026, 7, 1) if offset == 14 else date(2026, 7, 8)),
                )
            )
        self.db.commit()

        self.subject = subject
        self.teacher = teacher
        self.student = student
        self.classroom = classroom
        self.concept = concept
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
