from __future__ import annotations

import os
from datetime import date, datetime, timezone
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-learning-api-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import SignupRequest, create_user
from app.ai import DoubtChatContent, QuizGradeContent, TeachBackGradeContent, TutorialContent
from app.mastery import days_since_review, effective_mastery
from app.main import (
    DoubtChatRequest,
    QuizGradeRequest,
    TeachBackGradeRequest,
    TutorialRequest,
    concept_detail,
    demo_context,
    doubt_chat,
    grade_quiz,
    grade_teach_back_endpoint,
    recompute_forecasts,
    student_confusion_map,
    teacher_student_confusion_map,
    student_syllabus,
    student_report_card,
    tutorial,
    unlock_chapter,
)
from app.models import (
    Base,
    Chapter,
    ChapterUnlock,
    Classroom,
    ClassroomStudent,
    Concept,
    ConceptEdge,
    ForecastRecord,
    MasteryRecord,
    MisconceptionTaxonomy,
    Organization,
    QuizAttempt,
    Student,
    Subject,
    TeachBackAttempt,
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

    def test_student_report_card_uses_effective_mastery(self) -> None:
        report = student_report_card(self.student.id, current_user=self.teacher_user, db=self.db)
        self.assertEqual(report["student_name"], self.student.name)
        self.assertEqual(
            report["learning"][0]["mastery"],
            effective_mastery(0.68, days_since_review(datetime(2026, 7, 1, tzinfo=timezone.utc))),
        )

    def test_student_confusion_map_returns_mastery_nodes(self) -> None:
        graph = student_confusion_map(current_user=self.student_user, db=self.db)
        self.assertEqual([node.concept_id for node in graph.nodes], [self.unlocked_concept.id])
        self.assertEqual(graph.edges, [])

    def test_teacher_confusion_map_is_limited_to_their_classroom_student(self) -> None:
        graph = teacher_student_confusion_map(
            self.classroom.id, self.student.id, current_user=self.teacher_user, db=self.db
        )
        self.assertEqual([node.concept_id for node in graph.nodes], [self.unlocked_concept.id])
        self.assertEqual(graph.edges, [])

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

    def test_tutorial_generates_for_unlocked_concept_and_records_usage(self) -> None:
        with patch("app.main.generate_tutorial", return_value=TutorialContent("Explanation", "Analogy", "Example", "")) as generate:
            response = tutorial(
                concept_id=self.unlocked_concept.id,
                payload=TutorialRequest(reading_level="Class 10"),
                current_user=self.student_user,
                db=self.db,
            )

        self.assertEqual(response.explanation, "Explanation")
        self.assertEqual(response.worked_example, "Example")
        generate.assert_called_once()

    def test_tutorial_rejects_locked_concept_before_ai_call(self) -> None:
        with patch("app.main.generate_tutorial", return_value=TutorialContent("Explanation", "Analogy", "Example", "")) as generate:
            with self.assertRaises(HTTPException) as exc:
                tutorial(
                    concept_id=self.locked_concept.id,
                    payload=TutorialRequest(reading_level="Class 10"),
                    current_user=self.student_user,
                    db=self.db,
                )

        self.assertEqual(exc.exception.status_code, 403)
        generate.assert_not_called()

    def test_doubt_chat_uses_deterministic_scaffolding_response(self) -> None:
        with patch(
            "app.main.generate_doubt_response",
            return_value=DoubtChatContent(response="What should you balance first?", response_type="guiding_question"),
        ) as generate:
            response = doubt_chat(
                concept_id=self.unlocked_concept.id,
                payload=DoubtChatRequest(message="I do not get balancing.", turn_count=1),
                current_user=self.student_user,
                db=self.db,
            )

        self.assertEqual(response.response_type, "guiding_question")
        generate.assert_called_once()

    def test_doubt_chat_rejects_locked_concept_before_ai_call(self) -> None:
        with patch(
            "app.main.generate_doubt_response",
            return_value=DoubtChatContent(response="Hint", response_type="hint"),
        ) as generate:
            with self.assertRaises(HTTPException) as exc:
                doubt_chat(
                    concept_id=self.locked_concept.id,
                    payload=DoubtChatRequest(message="Help", turn_count=2),
                    current_user=self.student_user,
                    db=self.db,
                )

        self.assertEqual(exc.exception.status_code, 403)
        generate.assert_not_called()

    def test_teacher_cannot_use_doubt_chat(self) -> None:
        with patch(
            "app.main.generate_doubt_response",
            return_value=DoubtChatContent(response="Hint", response_type="hint"),
        ) as generate:
            with self.assertRaises(HTTPException) as exc:
                doubt_chat(
                    concept_id=self.unlocked_concept.id,
                    payload=DoubtChatRequest(message="Help", turn_count=2),
                    current_user=self.teacher_user,
                    db=self.db,
                )

        self.assertEqual(exc.exception.status_code, 403)
        generate.assert_not_called()

    def test_quiz_grade_stores_attempt_for_student(self) -> None:
        with patch(
            "app.main.grade_quiz_answer",
            return_value=QuizGradeContent(
                is_correct=False,
                misconception_code="BAL_SUBSCRIPT_CHANGE",
                misconception_summary="Changes subscripts instead of coefficients.",
                confidence=0.88,
                follow_up_question="What should change when balancing?",
            ),
        ) as grade:
            response = grade_quiz(
                concept_id=self.unlocked_concept.id,
                payload=QuizGradeRequest(
                    question="Balance H2 + O2 -> H2O",
                    student_answer="H2 + O2 -> H2O2",
                    rubric="2H2 + O2 -> 2H2O",
                ),
                current_user=self.student_user,
                db=self.db,
            )

        attempt = self.db.get(QuizAttempt, response.attempt_id)
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.misconception_code, "BAL_SUBSCRIPT_CHANGE")
        self.assertEqual(attempt.mode, "quiz")
        grade.assert_called_once()

    def test_teacher_cannot_submit_quiz_attempt(self) -> None:
        with patch(
            "app.main.grade_quiz_answer",
            return_value=QuizGradeContent(True, None, "Solid.", 0.95, "What is next?"),
        ) as grade:
            with self.assertRaises(HTTPException) as exc:
                grade_quiz(
                    concept_id=self.unlocked_concept.id,
                    payload=QuizGradeRequest(question="Q", student_answer="A", rubric="R"),
                    current_user=self.teacher_user,
                    db=self.db,
                )

        self.assertEqual(exc.exception.status_code, 403)
        grade.assert_not_called()

    def test_teach_back_grade_stores_attempt_for_student(self) -> None:
        with patch(
            "app.main.grade_teach_back",
            return_value=TeachBackGradeContent(
                clarity_score=0.72,
                accuracy_score=0.61,
                gap_identified="Misses conservation of atoms.",
                encouragement="Good start; explain atom count next.",
            ),
        ) as grade:
            response = grade_teach_back_endpoint(
                concept_id=self.unlocked_concept.id,
                payload=TeachBackGradeRequest(
                    student_explanation="Balancing means making the equation look equal.",
                    correct_summary="Balancing keeps atom counts equal on both sides using coefficients.",
                ),
                current_user=self.student_user,
                db=self.db,
            )

        attempt = self.db.get(TeachBackAttempt, response.attempt_id)
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.clarity_score, 0.72)
        self.assertIn("Misses conservation", attempt.gpt_feedback)
        grade.assert_called_once()

    def test_teacher_cannot_submit_teach_back_attempt(self) -> None:
        with patch(
            "app.main.grade_teach_back",
            return_value=TeachBackGradeContent(0.9, 0.9, "None.", "Clear."),
        ) as grade:
            with self.assertRaises(HTTPException) as exc:
                grade_teach_back_endpoint(
                    concept_id=self.unlocked_concept.id,
                    payload=TeachBackGradeRequest(student_explanation="A", correct_summary="B"),
                    current_user=self.teacher_user,
                    db=self.db,
                )

        self.assertEqual(exc.exception.status_code, 403)
        grade.assert_not_called()

    def test_teacher_can_recompute_forecasts_for_classroom(self) -> None:
        response = recompute_forecasts(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        stored_count = self.db.scalar(select(func.count(ForecastRecord.id)))

        self.assertEqual(response.classroom_id, self.classroom.id)
        self.assertEqual(response.forecast_count, 1)
        self.assertEqual(stored_count, 1)
        self.assertEqual(response.forecasts[0].concept_id, self.locked_concept.id)
        self.assertGreater(response.forecasts[0].predicted_difficulty, 0)

    def test_recompute_forecasts_replaces_existing_records(self) -> None:
        first = recompute_forecasts(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        second = recompute_forecasts(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        stored_count = self.db.scalar(select(func.count(ForecastRecord.id)))

        self.assertEqual(first.forecast_count, 1)
        self.assertEqual(second.forecast_count, 1)
        self.assertEqual(stored_count, 1)

    def test_recompute_forecasts_clears_stale_records_when_no_upcoming_concepts_remain(self) -> None:
        recompute_forecasts(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        self.db.add(ChapterUnlock(classroom_id=self.classroom.id, chapter_id=self.locked_chapter.id, unlocked_by=self.teacher.id))
        self.db.commit()

        response = recompute_forecasts(classroom_id=self.classroom.id, current_user=self.teacher_user, db=self.db)
        stored_count = self.db.scalar(select(func.count(ForecastRecord.id)))

        self.assertEqual(response.forecast_count, 0)
        self.assertEqual(stored_count, 0)

    def test_student_cannot_recompute_forecasts(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            recompute_forecasts(classroom_id=self.classroom.id, current_user=self.student_user, db=self.db)

        self.assertEqual(exc.exception.status_code, 403)

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
        self.db.add(ConceptEdge(concept_id=locked_concept.id, prerequisite_concept_id=unlocked_concept.id, weight=1.0))
        self.db.add(
            MasteryRecord(
                student_id=student.id,
                concept_id=unlocked_concept.id,
                quiz_accuracy_score=0.7,
                open_answer_score=0.6,
                misconception_recurrence=0.2,
                retention_score=0.8,
                computed_mastery=0.68,
                last_reviewed_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
                next_review_date=date(2026, 7, 20),
            )
        )
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
        org = Organization(name="Test School", slug="test-school", segment="school")
        self.db.add(org)
        self.db.flush()
        self.teacher_user.org_id = org.id
        self.student_user.org_id = org.id
        self.db.commit()
