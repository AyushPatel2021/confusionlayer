from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.mastery import days_since_review, effective_mastery
from app.models import Chapter, ChapterUnlock, Classroom, ClassroomStudent, Concept, ConceptEdge, ForecastRecord, MasteryRecord


@dataclass(frozen=True)
class PrerequisiteContribution:
    concept_id: int
    weight: float
    distance: int


@dataclass(frozen=True)
class ForecastContribution:
    concept_id: int
    title: str
    effective_mastery: float
    contribution_weight: float
    difficulty_component: float
    distance: int


@dataclass(frozen=True)
class ForecastResult:
    student_id: int
    concept_id: int
    predicted_difficulty: float
    contributing_concepts: list[ForecastContribution]


def forecast_difficulty(
    target_concept_id: int,
    student_id: int,
    prerequisites: dict[int, list[PrerequisiteContribution]],
    mastery_by_concept: dict[int, MasteryRecord],
    concept_titles: dict[int, str],
    today: date | None = None,
) -> ForecastResult:
    contributions: list[ForecastContribution] = []
    for prerequisite in prerequisites.get(target_concept_id, []):
        mastery = mastery_by_concept.get(prerequisite.concept_id)
        if not mastery:
            continue
        reviewed_days = days_since_review(mastery.last_reviewed_at, today)
        mastery_value = effective_mastery(mastery.computed_mastery, reviewed_days)
        difficulty_component = round((1 - mastery_value) * prerequisite.weight, 4)
        contributions.append(
            ForecastContribution(
                concept_id=prerequisite.concept_id,
                title=concept_titles.get(prerequisite.concept_id, f"Concept {prerequisite.concept_id}"),
                effective_mastery=mastery_value,
                contribution_weight=round(prerequisite.weight, 4),
                difficulty_component=difficulty_component,
                distance=prerequisite.distance,
            )
        )

    total_weight = sum(item.contribution_weight for item in contributions)
    if total_weight <= 0:
        predicted = 0.0
    else:
        predicted = round(sum(item.difficulty_component for item in contributions) / total_weight, 4)

    return ForecastResult(
        student_id=student_id,
        concept_id=target_concept_id,
        predicted_difficulty=predicted,
        contributing_concepts=sorted(contributions, key=lambda item: item.difficulty_component, reverse=True),
    )


def prerequisite_map(edges: list[ConceptEdge]) -> dict[int, list[PrerequisiteContribution]]:
    direct: dict[int, list[tuple[int, float]]] = {}
    for edge in edges:
        direct.setdefault(edge.concept_id, []).append((edge.prerequisite_concept_id, edge.weight))

    result: dict[int, list[PrerequisiteContribution]] = {}
    for concept_id in direct:
        weighted: dict[int, PrerequisiteContribution] = {}
        stack = [(concept_id, 1.0, 0, {concept_id})]
        while stack:
            current_id, path_weight, distance, seen = stack.pop()
            for prereq_id, edge_weight in direct.get(current_id, []):
                if prereq_id in seen:
                    continue
                next_distance = distance + 1
                hop_decay = 0.7 ** max(0, next_distance - 1)
                contribution_weight = path_weight * edge_weight * hop_decay
                existing = weighted.get(prereq_id)
                if existing is None or contribution_weight > existing.weight:
                    weighted[prereq_id] = PrerequisiteContribution(
                        concept_id=prereq_id,
                        weight=contribution_weight,
                        distance=next_distance,
                    )
                stack.append((prereq_id, path_weight * edge_weight, next_distance, seen | {prereq_id}))
        result[concept_id] = sorted(weighted.values(), key=lambda item: (item.distance, item.concept_id))
    return result


def recompute_classroom_forecasts(db: Session, classroom_id: int, today: date | None = None) -> list[ForecastRecord]:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        return []

    classroom_students = db.scalars(
        select(ClassroomStudent).where(ClassroomStudent.classroom_id == classroom_id).order_by(ClassroomStudent.student_id)
    ).all()
    student_ids = [item.student_id for item in classroom_students]
    if not student_ids:
        return []

    subject_concept_ids = list(
        db.scalars(select(Concept.id).join(Chapter, Chapter.id == Concept.chapter_id).where(Chapter.subject_id == classroom.subject_id)).all()
    )
    if not subject_concept_ids:
        return []

    unlocked_chapter_ids = set(db.scalars(select(ChapterUnlock.chapter_id).where(ChapterUnlock.classroom_id == classroom_id)).all())
    upcoming_concepts = db.scalars(
        select(Concept)
        .join(Chapter, Chapter.id == Concept.chapter_id)
        .where(Chapter.subject_id == classroom.subject_id, Chapter.id.not_in(unlocked_chapter_ids))
        .order_by(Chapter.order, Concept.order)
    ).all()
    upcoming_concept_ids = [concept.id for concept in upcoming_concepts]

    all_concepts = db.scalars(select(Concept)).all()
    concept_titles = {concept.id: concept.title for concept in all_concepts}
    prereqs = prerequisite_map(list(db.scalars(select(ConceptEdge)).all()))
    mastery_rows = db.scalars(select(MasteryRecord).where(MasteryRecord.student_id.in_(student_ids))).all()
    mastery_by_student: dict[int, dict[int, MasteryRecord]] = {}
    for mastery in mastery_rows:
        mastery_by_student.setdefault(mastery.student_id, {})[mastery.concept_id] = mastery

    db.execute(
        delete(ForecastRecord).where(
            ForecastRecord.student_id.in_(student_ids),
            ForecastRecord.concept_id.in_(subject_concept_ids),
        )
    )
    if not upcoming_concept_ids:
        db.commit()
        return []

    computed_at = datetime.now(UTC)
    records: list[ForecastRecord] = []
    for student_id in student_ids:
        for concept in upcoming_concepts:
            forecast = forecast_difficulty(
                target_concept_id=concept.id,
                student_id=student_id,
                prerequisites=prereqs,
                mastery_by_concept=mastery_by_student.get(student_id, {}),
                concept_titles=concept_titles,
                today=today,
            )
            record = ForecastRecord(
                student_id=student_id,
                concept_id=concept.id,
                predicted_difficulty=forecast.predicted_difficulty,
                contributing_concepts=[
                    {
                        "concept_id": item.concept_id,
                        "title": item.title,
                        "effective_mastery": item.effective_mastery,
                        "contribution_weight": item.contribution_weight,
                        "difficulty_component": item.difficulty_component,
                        "distance": item.distance,
                    }
                    for item in forecast.contributing_concepts
                ],
                computed_at=computed_at,
            )
            db.add(record)
            records.append(record)

    db.commit()
    for record in records:
        db.refresh(record)
    return records
