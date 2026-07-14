from __future__ import annotations

from datetime import date, datetime, timezone
from unittest import TestCase

from app.mastery import compute_mastery, days_since_review, decay_factor, effective_mastery


class MasteryFormulaTest(TestCase):
    def test_compute_mastery_uses_project_spec_weights(self) -> None:
        self.assertEqual(
            compute_mastery(
                quiz_accuracy_score=0.8,
                open_answer_score=0.6,
                misconception_recurrence=0.25,
                retention_score=0.9,
            ),
            0.7525,
        )

    def test_compute_mastery_rejects_out_of_range_scores(self) -> None:
        with self.assertRaises(ValueError):
            compute_mastery(1.1, 0.6, 0.25, 0.9)

        with self.assertRaises(ValueError):
            compute_mastery(0.8, 0.6, -0.1, 0.9)

    def test_decay_factor_floors_at_point_four(self) -> None:
        self.assertEqual(decay_factor(0), 1.0)
        self.assertEqual(decay_factor(10), 0.7)
        self.assertEqual(decay_factor(21), 0.4)
        self.assertEqual(decay_factor(60), 0.4)

    def test_effective_mastery_applies_decay(self) -> None:
        self.assertEqual(effective_mastery(0.75, 10), 0.525)
        self.assertEqual(effective_mastery(0.75, 60), 0.3)

    def test_days_since_review_accepts_date_or_datetime(self) -> None:
        today = date(2026, 7, 14)

        self.assertEqual(days_since_review(date(2026, 7, 1), today), 13)
        self.assertEqual(days_since_review(datetime(2026, 7, 10, tzinfo=timezone.utc), today), 4)

    def test_days_since_review_rejects_future_dates(self) -> None:
        with self.assertRaises(ValueError):
            days_since_review(date(2026, 7, 15), date(2026, 7, 14))
