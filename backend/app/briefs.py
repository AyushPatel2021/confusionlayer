"""Deterministic aggregation for the teacher-facing Confusion and Forecast briefs.

No AI runs here. These functions turn raw QuizAttempt / ForecastRecord rows into
the numbers the teacher screens display. GPT only ever writes the *narrative*
prose on top of these numbers (see app.ai), never the numbers themselves.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import Chapter, ClassroomStudent, Concept, ForecastRecord, MisconceptionTaxonomy, QuizAttempt

# A misconception is only ever surfaced to a teacher if at least this many
# distinct students share it (Section 9 privacy threshold — hard filter).
PRIVACY_THRESHOLD = 3

# A student is counted as "predicted to struggle" on an upcoming concept when
# their deterministic predicted_difficulty is at or above this value.
AT_RISK_THRESHOLD = 0.5


@dataclass(frozen=True)
class MisconceptionCluster:
    code: str
    description: str
    student_count: int


@dataclass(frozen=True)
class ConfusionConcept:
    concept_id: int
    concept_title: str
    chapter_title: str
    affected_student_count: int
    misconceptions: list[MisconceptionCluster]


@dataclass(frozen=True)
class ConfusionAggregate:
    classroom_id: int
    total_students: int
    privacy_threshold: int
    concepts: list[ConfusionConcept]


@dataclass(frozen=True)
class ForecastContributor:
    concept_id: int
    title: str
    average_effective_mastery: float
    mention_count: int


@dataclass(frozen=True)
class ForecastConcept:
    concept_id: int
    concept_title: str
    chapter_title: str
    at_risk_count: int
    total_students: int
    average_difficulty: float
    top_contributors: list[ForecastContributor]


@dataclass(frozen=True)
class ForecastAggregate:
    classroom_id: int
    total_students: int
    at_risk_threshold: float
    computed_at: datetime | None
    concepts: list[ForecastConcept]


def _classroom_student_ids(db: Session, classroom_id: int) -> list[int]:
    return list(
        db.scalars(select(ClassroomStudent.student_id).where(ClassroomStudent.classroom_id == classroom_id)).all()
    )


def aggregate_confusion(db: Session, classroom_id: int, threshold: int = PRIVACY_THRESHOLD) -> ConfusionAggregate:
    """Aggregate observed misconceptions across a classroom, privacy-filtered.

    Groups QuizAttempt misconception codes by (concept, code), counts *distinct*
    students, and drops any cluster shared by fewer than ``threshold`` students.
    No student identities are ever included in the result.
    """
    student_ids = _classroom_student_ids(db, classroom_id)
    total_students = len(student_ids)
    if not student_ids:
        return ConfusionAggregate(classroom_id, total_students, threshold, [])

    grouped = db.execute(
        select(
            QuizAttempt.concept_id,
            QuizAttempt.misconception_code,
            func.count(distinct(QuizAttempt.student_id)),
        )
        .where(
            QuizAttempt.student_id.in_(student_ids),
            QuizAttempt.misconception_code.is_not(None),
        )
        .group_by(QuizAttempt.concept_id, QuizAttempt.misconception_code)
    ).all()

    surfaced = [(concept_id, code, count) for concept_id, code, count in grouped if count >= threshold]
    if not surfaced:
        return ConfusionAggregate(classroom_id, total_students, threshold, [])

    concept_ids = {concept_id for concept_id, _, _ in surfaced}
    concept_meta = _concept_titles(db, concept_ids)
    descriptions = {
        (concept_id, code): description
        for concept_id, code, description in db.execute(
            select(MisconceptionTaxonomy.concept_id, MisconceptionTaxonomy.code, MisconceptionTaxonomy.description).where(
                MisconceptionTaxonomy.concept_id.in_(concept_ids)
            )
        ).all()
    }

    clusters_by_concept: dict[int, list[MisconceptionCluster]] = defaultdict(list)
    for concept_id, code, count in surfaced:
        clusters_by_concept[concept_id].append(
            MisconceptionCluster(code=code, description=descriptions.get((concept_id, code), ""), student_count=int(count))
        )

    concepts: list[ConfusionConcept] = []
    for concept_id, clusters in clusters_by_concept.items():
        clusters.sort(key=lambda item: item.student_count, reverse=True)
        concept_title, chapter_title = concept_meta.get(concept_id, (f"Concept {concept_id}", ""))
        affected = db.scalar(
            select(func.count(distinct(QuizAttempt.student_id))).where(
                QuizAttempt.concept_id == concept_id,
                QuizAttempt.student_id.in_(student_ids),
                QuizAttempt.misconception_code.in_([cluster.code for cluster in clusters]),
            )
        )
        concepts.append(
            ConfusionConcept(
                concept_id=concept_id,
                concept_title=concept_title,
                chapter_title=chapter_title,
                affected_student_count=int(affected or 0),
                misconceptions=clusters,
            )
        )

    concepts.sort(key=lambda item: item.affected_student_count, reverse=True)
    return ConfusionAggregate(classroom_id, total_students, threshold, concepts)


def aggregate_forecast(db: Session, classroom_id: int, at_risk_threshold: float = AT_RISK_THRESHOLD) -> ForecastAggregate:
    """Aggregate stored ForecastRecords for a classroom into per-concept summaries.

    Reads the deterministic predicted_difficulty rows produced by the forecast
    engine, counts how many students are at risk per upcoming concept, and rolls
    up which weak prerequisites are driving that risk across the at-risk cohort.
    """
    student_ids = _classroom_student_ids(db, classroom_id)
    total_students = len(student_ids)
    if not student_ids:
        return ForecastAggregate(classroom_id, 0, at_risk_threshold, None, [])

    records = list(db.scalars(select(ForecastRecord).where(ForecastRecord.student_id.in_(student_ids))).all())
    if not records:
        return ForecastAggregate(classroom_id, total_students, at_risk_threshold, None, [])

    records_by_concept: dict[int, list[ForecastRecord]] = defaultdict(list)
    for record in records:
        records_by_concept[record.concept_id].append(record)

    concept_meta = _concept_titles(db, set(records_by_concept))
    computed_at = max(record.computed_at for record in records)

    concepts: list[ForecastConcept] = []
    for concept_id, concept_records in records_by_concept.items():
        difficulties = [record.predicted_difficulty for record in concept_records]
        at_risk_count = sum(1 for value in difficulties if value >= at_risk_threshold)
        average_difficulty = round(sum(difficulties) / len(difficulties), 4)

        contributor_stats: dict[int, dict[str, float | str | int]] = {}
        for record in concept_records:
            if record.predicted_difficulty < at_risk_threshold:
                continue
            for item in record.contributing_concepts:
                prerequisite_id = int(item["concept_id"])
                stat = contributor_stats.setdefault(
                    prerequisite_id, {"title": str(item["title"]), "mastery_sum": 0.0, "count": 0}
                )
                stat["mastery_sum"] = float(stat["mastery_sum"]) + float(item["effective_mastery"])
                stat["count"] = int(stat["count"]) + 1

        contributors = [
            ForecastContributor(
                concept_id=prerequisite_id,
                title=str(stat["title"]),
                average_effective_mastery=round(float(stat["mastery_sum"]) / int(stat["count"]), 4),
                mention_count=int(stat["count"]),
            )
            for prerequisite_id, stat in contributor_stats.items()
        ]
        contributors.sort(key=lambda item: (-item.mention_count, item.average_effective_mastery))

        concept_title, chapter_title = concept_meta.get(concept_id, (f"Concept {concept_id}", ""))
        concepts.append(
            ForecastConcept(
                concept_id=concept_id,
                concept_title=concept_title,
                chapter_title=chapter_title,
                at_risk_count=at_risk_count,
                total_students=total_students,
                average_difficulty=average_difficulty,
                top_contributors=contributors[:3],
            )
        )

    concepts.sort(key=lambda item: (item.at_risk_count, item.average_difficulty), reverse=True)
    return ForecastAggregate(classroom_id, total_students, at_risk_threshold, computed_at, concepts)


def _concept_titles(db: Session, concept_ids: set[int]) -> dict[int, tuple[str, str]]:
    if not concept_ids:
        return {}
    rows = db.execute(
        select(Concept.id, Concept.title, Chapter.title)
        .join(Chapter, Chapter.id == Concept.chapter_id)
        .where(Concept.id.in_(concept_ids))
    ).all()
    return {concept_id: (concept_title, chapter_title) for concept_id, concept_title, chapter_title in rows}
