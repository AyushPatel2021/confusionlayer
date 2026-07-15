from __future__ import annotations

from datetime import date, datetime, timezone
from unittest import TestCase

from app.forecast import PrerequisiteContribution, forecast_difficulty, prerequisite_map
from app.models import ConceptEdge, MasteryRecord


class ForecastEngineTest(TestCase):
    def test_prerequisite_map_applies_multihop_decay(self) -> None:
        direct = ConceptEdge(concept_id=3, prerequisite_concept_id=2, weight=1.0)
        indirect = ConceptEdge(concept_id=2, prerequisite_concept_id=1, weight=0.5)

        prereqs = prerequisite_map([direct, indirect])

        self.assertEqual([item.concept_id for item in prereqs[3]], [2, 1])
        self.assertEqual(prereqs[3][0].weight, 1.0)
        self.assertAlmostEqual(prereqs[3][1].weight, 0.35)
        self.assertEqual(prereqs[3][1].distance, 2)

    def test_forecast_difficulty_uses_decayed_prerequisite_mastery(self) -> None:
        mastery = MasteryRecord(
            student_id=7,
            concept_id=1,
            quiz_accuracy_score=1,
            open_answer_score=1,
            misconception_recurrence=0,
            retention_score=1,
            computed_mastery=0.8,
            last_reviewed_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
            next_review_date=date(2026, 7, 20),
        )

        forecast = forecast_difficulty(
            target_concept_id=2,
            student_id=7,
            prerequisites={2: [PrerequisiteContribution(concept_id=1, weight=1.0, distance=1)]},
            mastery_by_concept={1: mastery},
            concept_titles={1: "Writing Chemical Equations"},
            today=date(2026, 7, 11),
        )

        self.assertEqual(forecast.predicted_difficulty, 0.44)
        self.assertEqual(forecast.contributing_concepts[0].effective_mastery, 0.56)

    def test_forecast_difficulty_rises_when_review_is_stale(self) -> None:
        recent = MasteryRecord(
            student_id=7,
            concept_id=1,
            quiz_accuracy_score=1,
            open_answer_score=1,
            misconception_recurrence=0,
            retention_score=1,
            computed_mastery=0.8,
            last_reviewed_at=datetime(2026, 7, 10, tzinfo=timezone.utc),
            next_review_date=date(2026, 7, 20),
        )
        stale = MasteryRecord(
            student_id=8,
            concept_id=1,
            quiz_accuracy_score=1,
            open_answer_score=1,
            misconception_recurrence=0,
            retention_score=1,
            computed_mastery=0.8,
            last_reviewed_at=datetime(2026, 6, 10, tzinfo=timezone.utc),
            next_review_date=date(2026, 7, 20),
        )
        prereqs = {2: [PrerequisiteContribution(concept_id=1, weight=1.0, distance=1)]}

        recent_forecast = forecast_difficulty(2, 7, prereqs, {1: recent}, {1: "Concept"}, date(2026, 7, 11))
        stale_forecast = forecast_difficulty(2, 8, prereqs, {1: stale}, {1: "Concept"}, date(2026, 7, 11))

        self.assertGreater(stale_forecast.predicted_difficulty, recent_forecast.predicted_difficulty)
