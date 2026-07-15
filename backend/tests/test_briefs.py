from __future__ import annotations

import os
from datetime import UTC, date, datetime
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-briefs-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai import BriefNarrativeContent
from app.auth import SignupRequest, create_user
from app.main import (
    BriefNarrativeRequest,
    confusion_brief,
    confusion_brief_narrative,
    forecast_brief,
    forecast_brief_narrative,
)
from app.models import (
    Base,
    Chapter,
    Classroom,
    ClassroomStudent,
    Concept,
    ConfusionBrief,
    ForecastRecord,
    MisconceptionTaxonomy,
    QuizAttempt,
    Student,
    Subject,
    Teacher,
)


class BriefsTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db: Session = self.session_factory()
        self._seed_classroom()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    # ---- Confusion brief -------------------------------------------------

    def test_confusion_brief_surfaces_only_clusters_meeting_threshold(self) -> None:
        response = confusion_brief(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)

        # Concept A: code SHARED_3 has 3 students (surfaced); code RARE_2 has 2 (hidden).
        self.assertEqual(response.total_students, 4)
        self.assertEqual(response.privacy_threshold, 3)
        self.assertEqual(len(response.concepts), 1)
        concept = response.concepts[0]
        self.assertEqual(concept.concept_id, self.concept_a.id)
        codes = {item.code for item in concept.misconceptions}
        self.assertEqual(codes, {"SHARED_3"})
        self.assertEqual(concept.misconceptions[0].student_count, 3)
        self.assertEqual(concept.affected_student_count, 3)

    def test_confusion_brief_hides_below_threshold_cluster(self) -> None:
        response = confusion_brief(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        all_codes = {item.code for concept in response.concepts for item in concept.misconceptions}
        self.assertNotIn("RARE_2", all_codes)

    def test_confusion_brief_never_includes_student_identifiers(self) -> None:
        response = confusion_brief(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        payload = response.model_dump_json()
        for name in ("Aarav", "Diya", "Kabir", "Meera"):
            self.assertNotIn(name, payload)

    def test_confusion_brief_blocks_students(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            confusion_brief(classroom_id=self.classroom.id, current_user=self.student_user, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_confusion_narrative_generates_and_persists(self) -> None:
        with patch(
            "app.main.generate_confusion_narrative",
            return_value=BriefNarrativeContent(summary="3 students confuse the idea.", suggested_activity="7-min recap."),
        ) as narrate:
            response = confusion_brief_narrative(
                classroom_id=self.classroom.id,
                payload=BriefNarrativeRequest(concept_id=self.concept_a.id),
                current_user=self.teacher_user,
                db=self.db,
            )

        narrate.assert_called_once()
        self.assertEqual(response.concept_id, self.concept_a.id)
        self.assertEqual(response.summary, "3 students confuse the idea.")
        stored = self.db.query(ConfusionBrief).all()
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].affected_student_count, 3)
        self.assertEqual(stored[0].misconception_breakdown, {"SHARED_3": 3})

    def test_confusion_narrative_rejects_concept_below_threshold(self) -> None:
        with patch("app.main.generate_confusion_narrative") as narrate:
            with self.assertRaises(HTTPException) as exc:
                confusion_brief_narrative(
                    classroom_id=self.classroom.id,
                    payload=BriefNarrativeRequest(concept_id=self.concept_b.id),
                    current_user=self.teacher_user,
                    db=self.db,
                )
        self.assertEqual(exc.exception.status_code, 404)
        narrate.assert_not_called()

    # ---- Forecast brief --------------------------------------------------

    def test_forecast_brief_counts_at_risk_students_and_contributors(self) -> None:
        response = forecast_brief(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)

        self.assertEqual(response.total_students, 4)
        self.assertEqual(response.at_risk_threshold, 0.5)
        self.assertEqual(len(response.concepts), 1)
        concept = response.concepts[0]
        self.assertEqual(concept.concept_id, self.concept_b.id)
        # 2 of the students have predicted_difficulty >= 0.5 (0.8 and 0.6).
        self.assertEqual(concept.at_risk_count, 2)
        self.assertEqual(concept.total_students, 4)
        self.assertGreater(len(concept.top_contributors), 0)
        self.assertEqual(concept.top_contributors[0].title, "Concept A")

    def test_forecast_brief_empty_when_no_records(self) -> None:
        self.db.query(ForecastRecord).delete()
        self.db.commit()
        response = forecast_brief(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        self.assertEqual(response.concepts, [])
        self.assertIsNone(response.computed_at)

    def test_forecast_brief_blocks_students(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            forecast_brief(classroom_id=self.classroom.id, current_user=self.student_user, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_forecast_narrative_generates(self) -> None:
        with patch(
            "app.main.generate_forecast_narrative",
            return_value=BriefNarrativeContent(summary="2 of 4 predicted to struggle.", suggested_activity="5-min recap."),
        ) as narrate:
            response = forecast_brief_narrative(
                classroom_id=self.classroom.id,
                payload=BriefNarrativeRequest(concept_id=self.concept_b.id),
                current_user=self.teacher_user,
                db=self.db,
            )
        narrate.assert_called_once()
        self.assertEqual(response.concept_id, self.concept_b.id)
        self.assertIn("struggle", response.summary)

    def test_forecast_narrative_rejects_unknown_concept(self) -> None:
        with patch("app.main.generate_forecast_narrative") as narrate:
            with self.assertRaises(HTTPException) as exc:
                forecast_brief_narrative(
                    classroom_id=self.classroom.id,
                    payload=BriefNarrativeRequest(concept_id=self.concept_a.id),
                    current_user=self.teacher_user,
                    db=self.db,
                )
        self.assertEqual(exc.exception.status_code, 404)
        narrate.assert_not_called()

    # ---- Seed ------------------------------------------------------------

    def _seed_classroom(self) -> None:
        subject = Subject(name="CBSE Class 10 Science", board="CBSE", class_level="10")
        teacher = Teacher(name="Teacher One")
        self.db.add_all([subject, teacher])
        self.db.flush()

        students = [Student(name=name) for name in ("Aarav", "Diya", "Kabir", "Meera")]
        self.db.add_all(students)
        self.db.flush()

        classroom = Classroom(name="Class 10A", teacher_id=teacher.id, subject_id=subject.id)
        self.db.add(classroom)
        self.db.flush()
        for student in students:
            self.db.add(ClassroomStudent(classroom_id=classroom.id, student_id=student.id))

        chapter_a = Chapter(subject_id=subject.id, title="Chapter A", order=1)
        chapter_b = Chapter(subject_id=subject.id, title="Chapter B", order=2)
        self.db.add_all([chapter_a, chapter_b])
        self.db.flush()

        concept_a = Concept(chapter_id=chapter_a.id, title="Concept A", order=1)
        concept_b = Concept(chapter_id=chapter_b.id, title="Concept B", order=1)
        self.db.add_all([concept_a, concept_b])
        self.db.flush()

        self.db.add(MisconceptionTaxonomy(concept_id=concept_a.id, code="SHARED_3", description="Shared misconception."))
        self.db.add(MisconceptionTaxonomy(concept_id=concept_a.id, code="RARE_2", description="Rare misconception."))

        # Concept A confusion: SHARED_3 shown by 3 students, RARE_2 by 2 students.
        for student in students[:3]:
            self.db.add(self._attempt(student.id, concept_a.id, "SHARED_3"))
        for student in students[:2]:
            self.db.add(self._attempt(student.id, concept_a.id, "RARE_2"))

        # Forecast records on upcoming Concept B: 2 of 4 students at/above 0.5.
        difficulties = [0.8, 0.6, 0.3, 0.1]
        for student, difficulty in zip(students, difficulties):
            self.db.add(
                ForecastRecord(
                    student_id=student.id,
                    concept_id=concept_b.id,
                    predicted_difficulty=difficulty,
                    contributing_concepts=[
                        {
                            "concept_id": concept_a.id,
                            "title": "Concept A",
                            "effective_mastery": 0.3,
                            "contribution_weight": 1.0,
                            "difficulty_component": 0.7,
                            "distance": 1,
                        }
                    ],
                    computed_at=datetime(2026, 7, 15, tzinfo=UTC),
                )
            )

        self.db.commit()

        self.subject = subject
        self.teacher = teacher
        self.classroom = classroom
        self.concept_a = concept_a
        self.concept_b = concept_b
        self.teacher_user = create_user(
            self.db,
            SignupRequest(email="teacher@example.com", password="password123", role="teacher", name="Teacher Login"),
        )
        self.teacher_user.teacher_id = teacher.id
        self.student_user = create_user(
            self.db,
            SignupRequest(email="student@example.com", password="password123", role="student", name="Student Login"),
        )
        self.student_user.student_id = students[0].id
        self.db.commit()

    def _attempt(self, student_id: int, concept_id: int, code: str) -> QuizAttempt:
        return QuizAttempt(
            student_id=student_id,
            concept_id=concept_id,
            question="Q",
            student_answer="A",
            is_correct=False,
            misconception_code=code,
            confidence=0.8,
            mode="quiz",
        )
