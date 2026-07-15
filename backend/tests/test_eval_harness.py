from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-eval-tests")

from app.eval.dataset import (
    CORRECT_CASES,
    DOUBT_LEAK_CASES,
    DOUBT_OFFTOPIC_CASES,
    GRADER_CASES,
    MISCONCEPTION_CASES,
    PARTIAL_CASES,
)
from app.eval.run_eval import (
    DoubtResult,
    GraderResult,
    is_leak,
    score_doubt_leak,
    score_doubt_offtopic,
    score_grader,
)


class EvalDatasetTest(TestCase):
    def test_dataset_has_the_specified_sizes(self) -> None:
        self.assertEqual(len(CORRECT_CASES), 10)
        self.assertEqual(len(PARTIAL_CASES), 10)
        self.assertEqual(len(MISCONCEPTION_CASES), 10)
        self.assertEqual(len(GRADER_CASES), 30)
        self.assertEqual(len(DOUBT_OFFTOPIC_CASES), 5)
        self.assertEqual(len(DOUBT_LEAK_CASES), 5)

    def test_misconception_cases_reference_a_code(self) -> None:
        for case in MISCONCEPTION_CASES:
            self.assertIsNotNone(case.expected_misconception_code)
            self.assertFalse(case.expected_correct)


class EvalScoringTest(TestCase):
    def test_score_grader_perfect_run(self) -> None:
        results = []
        for case in GRADER_CASES:
            if case.category == "correct":
                results.append(GraderResult(True, True, None))
            elif case.category == "misconception":
                results.append(GraderResult(True, False, case.expected_misconception_code))
            else:  # partial
                results.append(GraderResult(True, False, None))

        metrics = score_grader(GRADER_CASES, results)
        self.assertEqual(metrics["structured_output_success"], (30, 30))
        self.assertEqual(metrics["correctness_classification"], (20, 20))
        self.assertEqual(metrics["misconception_code_match"], (10, 10))
        self.assertEqual(metrics["partial_graceful"], (10, 10))

    def test_score_grader_counts_wrong_code_and_failures(self) -> None:
        results = []
        for case in GRADER_CASES:
            if case.category == "correct":
                results.append(GraderResult(True, True, None))
            elif case.category == "misconception":
                results.append(GraderResult(True, False, "WRONG_CODE"))  # code miss
            else:
                results.append(GraderResult(False, None, None))  # partial: structured failure

        metrics = score_grader(GRADER_CASES, results)
        self.assertEqual(metrics["misconception_code_match"], (0, 10))
        self.assertEqual(metrics["partial_graceful"], (0, 10))
        self.assertEqual(metrics["structured_output_success"], (20, 30))
        # correct cases still classified right; misconception is_correct still False -> 20/20
        self.assertEqual(metrics["correctness_classification"], (20, 20))

    def test_leak_detection(self) -> None:
        clean = DoubtResult("What do you think happens first?", "guiding_question", True)
        leaked = DoubtResult("The answer is 2H2 + O2 -> 2H2O.", "explanation", True)
        self.assertFalse(is_leak(clean))
        self.assertTrue(is_leak(leaked))
        self.assertEqual(score_doubt_leak([clean, clean, leaked]), (1, 3))

    def test_offtopic_redirect_counts_guiding_questions(self) -> None:
        results = [
            DoubtResult("Let's refocus — what does the concept say?", "guiding_question", True),
            DoubtResult("Sure, the capital is Paris.", "explanation", True),
        ]
        self.assertEqual(score_doubt_offtopic(results), (1, 2))
