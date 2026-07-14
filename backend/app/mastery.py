from __future__ import annotations

from datetime import date, datetime


def _validate_score(name: str, value: float) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{name} must be between 0 and 1")


def compute_mastery(
    quiz_accuracy_score: float,
    open_answer_score: float,
    misconception_recurrence: float,
    retention_score: float,
) -> float:
    _validate_score("quiz_accuracy_score", quiz_accuracy_score)
    _validate_score("open_answer_score", open_answer_score)
    _validate_score("misconception_recurrence", misconception_recurrence)
    _validate_score("retention_score", retention_score)

    return round(
        0.50 * quiz_accuracy_score
        + 0.25 * open_answer_score
        + 0.15 * (1 - misconception_recurrence)
        + 0.10 * retention_score,
        4,
    )


def decay_factor(days_since_last_reviewed: int) -> float:
    if days_since_last_reviewed < 0:
        raise ValueError("days_since_last_reviewed must be non-negative")
    return max(0.4, round(1 - 0.03 * days_since_last_reviewed, 4))


def effective_mastery(computed_mastery: float, days_since_last_reviewed: int) -> float:
    _validate_score("computed_mastery", computed_mastery)
    return round(computed_mastery * decay_factor(days_since_last_reviewed), 4)


def days_since_review(last_reviewed_at: datetime | date, today: date | None = None) -> int:
    reference_date = today or date.today()
    reviewed_date = last_reviewed_at.date() if isinstance(last_reviewed_at, datetime) else last_reviewed_at
    days = (reference_date - reviewed_date).days
    if days < 0:
        raise ValueError("last_reviewed_at cannot be in the future")
    return days
