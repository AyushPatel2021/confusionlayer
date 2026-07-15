from __future__ import annotations

import os
from datetime import date
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-ai-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.ai import (
    QuizGradeContent,
    check_and_increment_ai_usage,
    doubt_response_type,
    grade_quiz_answer,
    parse_doubt_response,
    parse_quiz_grade_response,
    parse_tutorial_response,
)
from app.auth import SignupRequest, create_user
from app.models import AiCallUsage, Base


class AiUsageTest(TestCase):
    def setUp(self) -> None:
        os.environ["AI_DAILY_CALL_LIMIT"] = "2"
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db: Session = self.session_factory()
        self.user = create_user(
            self.db,
            SignupRequest(email="student@example.com", password="password123", role="admin", name="Admin"),
        )

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_check_and_increment_ai_usage_counts_per_user_per_day(self) -> None:
        usage_date = date(2026, 7, 15)

        first = check_and_increment_ai_usage(self.db, self.user, usage_date)
        second = check_and_increment_ai_usage(self.db, self.user, usage_date)

        self.assertEqual(first.id, second.id)
        self.assertEqual(second.call_count, 2)
        self.assertEqual(self.db.query(AiCallUsage).count(), 1)

    def test_check_and_increment_ai_usage_enforces_daily_limit(self) -> None:
        usage_date = date(2026, 7, 15)
        check_and_increment_ai_usage(self.db, self.user, usage_date)
        check_and_increment_ai_usage(self.db, self.user, usage_date)

        with self.assertRaises(HTTPException) as exc:
            check_and_increment_ai_usage(self.db, self.user, usage_date)

        self.assertEqual(exc.exception.status_code, 429)

    def test_parse_tutorial_response_accepts_output_text_json(self) -> None:
        tutorial = parse_tutorial_response(
            {
                "output_text": '{"explanation": "A focused explanation.", "worked_example": "A worked example."}',
            }
        )

        self.assertEqual(tutorial.explanation, "A focused explanation.")
        self.assertEqual(tutorial.worked_example, "A worked example.")

    def test_parse_tutorial_response_accepts_codex_final_message_json(self) -> None:
        tutorial = parse_tutorial_response(
            '{"explanation": "A Codex explanation.", "worked_example": "A Codex worked example."}'
        )

        self.assertEqual(tutorial.explanation, "A Codex explanation.")
        self.assertEqual(tutorial.worked_example, "A Codex worked example.")

    def test_parse_tutorial_response_rejects_bad_contract(self) -> None:
        with self.assertRaises(HTTPException):
            parse_tutorial_response({"output_text": '{"explanation": "Missing example."}'})

    def test_doubt_response_type_is_deterministic(self) -> None:
        self.assertEqual(doubt_response_type(1), "guiding_question")
        self.assertEqual(doubt_response_type(2), "hint")
        self.assertEqual(doubt_response_type(3), "worked_step")
        self.assertEqual(doubt_response_type(4), "explanation")

    def test_parse_doubt_response_accepts_contract(self) -> None:
        response = parse_doubt_response('{"response": "What changes first?", "response_type": "guiding_question"}')

        self.assertEqual(response.response_type, "guiding_question")

    def test_parse_quiz_grade_response_accepts_contract(self) -> None:
        grade = parse_quiz_grade_response(
            '{"is_correct": false, "misconception_code": "BAL_SUBSCRIPT_CHANGE", '
            '"misconception_summary": "Changes subscripts.", "confidence": 0.86, '
            '"follow_up_question": "What should change instead?"}'
        )

        self.assertEqual(grade.misconception_code, "BAL_SUBSCRIPT_CHANGE")
        self.assertAlmostEqual(grade.confidence, 0.86)

    def test_grade_quiz_answer_rejects_code_outside_taxonomy(self) -> None:
        class SubjectStub:
            board = "CBSE"
            class_level = "10"
            name = "Science"

        class ChapterStub:
            title = "Chemical Reactions"
            subject = SubjectStub()

        class ConceptStub:
            title = "Balancing Chemical Equations"
            chapter = ChapterStub()

        def fake_run_codex_json(_prompt: str, _schema_filename: str) -> str:
            return (
                '{"is_correct": false, "misconception_code": "INVENTED_CODE", '
                '"misconception_summary": "Invented.", "confidence": 0.75, "follow_up_question": "Try again?"}'
            )

        from unittest.mock import patch

        with patch("app.ai._run_codex_json", side_effect=fake_run_codex_json):
            with self.assertRaises(HTTPException) as exc:
                grade_quiz_answer(
                    ConceptStub(),  # type: ignore[arg-type]
                    "Question",
                    "Answer",
                    "Rubric",
                    [{"code": "BAL_SUBSCRIPT_CHANGE", "description": "Changes subscripts."}],
                )

        self.assertEqual(exc.exception.status_code, 502)
