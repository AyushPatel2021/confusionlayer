from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.db import SessionLocal, engine
from app.mastery import compute_mastery
from app.models import (
    AdmissionApplication,
    AttendanceRecord,
    AuditLog,
    Base,
    Chapter,
    ChapterUnlock,
    Classroom,
    ClassroomStudent,
    Concept,
    ConceptEdge,
    Designation,
    Employee,
    FeeStructure,
    ForecastRecord,
    GuardianLink,
    Invoice,
    InvoiceLineItem,
    MasteryHistory,
    MasteryRecord,
    MisconceptionTaxonomy,
    Notification,
    Organization,
    Payment,
    Plan,
    PayrollRun,
    Payslip,
    QuizAttempt,
    SalaryStructure,
    Student,
    Subject,
    Subscription,
    Teacher,
    TeachBackAttempt,
    TimetableEntry,
    User,
)


@dataclass(frozen=True)
class ConceptSeed:
    chapter: str
    title: str
    order: int
    misconceptions: tuple[tuple[str, str], ...]


CHAPTERS = (
    ("Chemical Reactions and Equations", 1),
    ("Acids, Bases and Salts", 2),
    ("Metals and Non-metals", 3),
)

CONCEPTS = (
    ConceptSeed(
        "Chemical Reactions and Equations",
        "Writing Chemical Equations",
        1,
        (
            ("EQN_SYMBOL_CONFUSION", "Confuses chemical symbols or formulae while writing equations."),
            ("EQN_REACTANT_PRODUCT_SWAP", "Swaps reactants and products in a reaction equation."),
            ("EQN_STATE_SYMBOL_MISSING", "Omits or misuses state symbols in equations."),
        ),
    ),
    ConceptSeed(
        "Chemical Reactions and Equations",
        "Balancing Chemical Equations",
        2,
        (
            ("BAL_SUBSCRIPT_CHANGE", "Changes subscripts instead of coefficients while balancing."),
            ("BAL_ATOM_COUNT_MISMATCH", "Does not conserve atom counts across both sides."),
            ("BAL_COEFFICIENT_RATIO_ERROR", "Uses coefficients that do not preserve the simplest whole-number ratio."),
        ),
    ),
    ConceptSeed(
        "Chemical Reactions and Equations",
        "Types of Chemical Reactions",
        3,
        (
            ("RXN_TYPE_COMB_DECOMP_SWAP", "Confuses combination and decomposition reactions."),
            ("RXN_DISPLACEMENT_MISREAD", "Misidentifies displacement reactions as simple mixing."),
            ("RXN_DOUBLE_DISPLACEMENT_PRECIPITATE", "Misses precipitate formation in double displacement reactions."),
        ),
    ),
    ConceptSeed(
        "Chemical Reactions and Equations",
        "Oxidation and Reduction",
        4,
        (
            ("REDOX_OXYGEN_ONLY", "Thinks oxidation and reduction are only about oxygen transfer."),
            ("REDOX_ELECTRON_DIRECTION", "Reverses electron loss and gain definitions."),
            ("REDOX_AGENT_ROLE_SWAP", "Swaps oxidising and reducing agent roles."),
        ),
    ),
    ConceptSeed(
        "Chemical Reactions and Equations",
        "Corrosion and Rancidity",
        5,
        (
            ("CORROSION_RUST_ONLY", "Assumes corrosion only means rusting of iron."),
            ("RANCIDITY_MICROBE_CONFUSION", "Confuses oxidation of fats with microbial spoilage."),
            ("PREVENTION_METHOD_MISMATCH", "Matches prevention methods to the wrong process."),
        ),
    ),
    ConceptSeed(
        "Acids, Bases and Salts",
        "Acid and Base Indicators",
        1,
        (
            ("INDICATOR_COLOR_REVERSAL", "Reverses indicator color changes for acids and bases."),
            ("INDICATOR_PH_CONFUSION", "Treats indicator color as the same thing as pH value."),
            ("INDICATOR_UNIVERSAL_RANGE", "Misreads universal indicator as only acidic or basic."),
        ),
    ),
    ConceptSeed(
        "Acids, Bases and Salts",
        "pH Scale",
        2,
        (
            ("PH_LINEAR_SCALE", "Thinks each pH unit changes acidity linearly instead of logarithmically."),
            ("PH_NEUTRAL_RANGE_ERROR", "Treats any value near 7 as exactly neutral."),
            ("PH_STRENGTH_CONCENTRATION_CONFUSION", "Confuses acid strength with concentration."),
        ),
    ),
    ConceptSeed(
        "Acids, Bases and Salts",
        "Neutralisation Reactions",
        3,
        (
            ("NEUTRAL_SALT_ALWAYS_NACL", "Assumes every neutralisation reaction produces sodium chloride."),
            ("NEUTRAL_WATER_MISSING", "Forgets water as a product of neutralisation."),
            ("NEUTRAL_COMPLETE_PH7", "Assumes every neutralisation mixture ends at pH 7."),
        ),
    ),
    ConceptSeed(
        "Acids, Bases and Salts",
        "Salts and Their Preparation",
        4,
        (
            ("SALT_SOURCE_ION_ERROR", "Cannot identify which ions form the salt."),
            ("SALT_PREP_METHOD_SWAP", "Chooses an inappropriate preparation method for a salt."),
            ("SALT_SOLUBILITY_IGNORED", "Ignores solubility while selecting a preparation route."),
        ),
    ),
    ConceptSeed(
        "Acids, Bases and Salts",
        "Water of Crystallisation",
        5,
        (
            ("CRYSTAL_WATER_FREE_WATER", "Treats water of crystallisation as loose surface water."),
            ("CRYSTAL_COLOR_REASON_ERROR", "Misses the role of bound water in crystal color."),
            ("CRYSTAL_HEATING_REVERSAL", "Misstates what heating hydrated salts removes."),
        ),
    ),
    ConceptSeed(
        "Metals and Non-metals",
        "Physical Properties of Metals",
        1,
        (
            ("METAL_PROPERTY_ABSOLUTE", "Treats all metal properties as absolute with no exceptions."),
            ("DUCTILE_MALLEABLE_SWAP", "Confuses ductility with malleability."),
            ("CONDUCTIVITY_NONMETAL_EXCEPTION", "Misses graphite and other conductivity exceptions."),
        ),
    ),
    ConceptSeed(
        "Metals and Non-metals",
        "Reactivity Series",
        2,
        (
            ("RXN_ELECTRONEGATIVITY_CONFUSION", "Confuses electronegativity trend with metallic reactivity trend."),
            ("REACTIVITY_POSITION_REVERSAL", "Reads the reactivity series in the wrong direction."),
            ("DISPLACEMENT_RULE_ERROR", "Does not apply the rule that a more reactive metal displaces a less reactive one."),
        ),
    ),
    ConceptSeed(
        "Metals and Non-metals",
        "Ionic Bonding",
        3,
        (
            ("IONIC_SHARE_CONFUSION", "Describes ionic bonding as electron sharing instead of transfer."),
            ("ION_CHARGE_SIGN_ERROR", "Assigns cation or anion charges in the wrong direction."),
            ("IONIC_OCTET_OVERFOCUS", "Mentions octet completion without explaining electrostatic attraction."),
        ),
    ),
    ConceptSeed(
        "Metals and Non-metals",
        "Extraction of Metals",
        4,
        (
            ("EXTRACTION_REACTIVITY_IGNORED", "Does not connect extraction method to metal reactivity."),
            ("ORE_MINERAL_SWAP", "Confuses ores with minerals."),
            ("REDUCTION_METHOD_MISMATCH", "Chooses carbon reduction for metals too high in the reactivity series."),
        ),
    ),
    ConceptSeed(
        "Metals and Non-metals",
        "Corrosion Prevention",
        5,
        (
            ("GALVANISING_PAINTING_SWAP", "Confuses galvanising with painting."),
            ("ALLOY_PURPOSE_ERROR", "Misses why alloying can reduce corrosion."),
            ("BARRIER_SACRIFICIAL_CONFUSION", "Confuses barrier protection with sacrificial protection."),
        ),
    ),
)

EDGES = (
    ("Balancing Chemical Equations", "Writing Chemical Equations", 1.0),
    ("Types of Chemical Reactions", "Balancing Chemical Equations", 0.8),
    ("Oxidation and Reduction", "Types of Chemical Reactions", 0.9),
    ("Corrosion and Rancidity", "Oxidation and Reduction", 0.8),
    ("pH Scale", "Acid and Base Indicators", 0.7),
    ("Neutralisation Reactions", "pH Scale", 1.0),
    ("Salts and Their Preparation", "Neutralisation Reactions", 0.9),
    ("Water of Crystallisation", "Salts and Their Preparation", 0.7),
    ("Reactivity Series", "Oxidation and Reduction", 0.8),
    ("Reactivity Series", "Types of Chemical Reactions", 0.7),
    ("Ionic Bonding", "Reactivity Series", 1.0),
    ("Ionic Bonding", "pH Scale", 0.4),
    ("Extraction of Metals", "Reactivity Series", 1.0),
    ("Corrosion Prevention", "Corrosion and Rancidity", 0.9),
    ("Corrosion Prevention", "Reactivity Series", 0.7),
)

STUDENT_NAMES = (
    "Aarav Mehta",
    "Diya Shah",
    "Kabir Nair",
    "Anika Rao",
    "Ishaan Iyer",
    "Meera Kulkarni",
    "Rohan Das",
    "Sara Khan",
    "Vivaan Singh",
    "Tara Menon",
)

QUIZ_ATTEMPTS = (
    ("Aarav Mehta", "Reactivity Series", "Which metal displaces copper from copper sulphate?", "Aluminium, because it is more electronegative.", False, "RXN_ELECTRONEGATIVITY_CONFUSION", 0.91),
    ("Diya Shah", "Reactivity Series", "Why does zinc displace copper?", "Zinc attracts electrons more strongly than copper.", False, "RXN_ELECTRONEGATIVITY_CONFUSION", 0.88),
    ("Kabir Nair", "Reactivity Series", "Which is more reactive, sodium or aluminium?", "Aluminium because it has more valence electrons.", False, "RXN_ELECTRONEGATIVITY_CONFUSION", 0.86),
    ("Anika Rao", "Reactivity Series", "Can iron displace copper?", "No, because copper is above iron in the list.", False, "REACTIVITY_POSITION_REVERSAL", 0.84),
    ("Ishaan Iyer", "Reactivity Series", "What does the reactivity series show?", "The bottom metals are most reactive.", False, "REACTIVITY_POSITION_REVERSAL", 0.82),
    ("Meera Kulkarni", "Balancing Chemical Equations", "Balance H2 + O2 -> H2O.", "H2 + O2 -> H2O2", False, "BAL_SUBSCRIPT_CHANGE", 0.9),
    ("Rohan Das", "Balancing Chemical Equations", "Balance Mg + O2 -> MgO.", "Mg + O2 -> MgO2", False, "BAL_SUBSCRIPT_CHANGE", 0.87),
    ("Sara Khan", "Balancing Chemical Equations", "Balance N2 + H2 -> NH3.", "N2 + H2 -> N2H2", False, "BAL_SUBSCRIPT_CHANGE", 0.83),
    ("Vivaan Singh", "Neutralisation Reactions", "What forms when acid reacts with base?", "Only salt forms.", False, "NEUTRAL_WATER_MISSING", 0.81),
    ("Tara Menon", "Neutralisation Reactions", "Name products of HCl and NaOH.", "NaCl only.", False, "NEUTRAL_WATER_MISSING", 0.79),
    ("Aarav Mehta", "Neutralisation Reactions", "Does neutralisation always end at pH 7?", "Yes, all neutralisation ends at pH 7.", False, "NEUTRAL_COMPLETE_PH7", 0.76),
    ("Diya Shah", "pH Scale", "How different are pH 3 and pH 4?", "pH 3 is one unit more acidic, so just slightly stronger.", False, "PH_LINEAR_SCALE", 0.89),
    ("Kabir Nair", "pH Scale", "What does pH 2 mean?", "It is twice as acidic as pH 4.", False, "PH_LINEAR_SCALE", 0.85),
    ("Anika Rao", "Ionic Bonding", "How does NaCl form?", "Sodium and chlorine share electrons equally.", False, "IONIC_SHARE_CONFUSION", 0.9),
    ("Ishaan Iyer", "Ionic Bonding", "Describe ionic bonding.", "Two atoms share electrons to complete octets.", False, "IONIC_SHARE_CONFUSION", 0.88),
    ("Meera Kulkarni", "Ionic Bonding", "What charge does sodium form?", "Sodium gains an electron and becomes negative.", False, "ION_CHARGE_SIGN_ERROR", 0.82),
    ("Rohan Das", "Oxidation and Reduction", "What is reduction?", "Reduction is always adding oxygen.", False, "REDOX_OXYGEN_ONLY", 0.84),
    ("Sara Khan", "Oxidation and Reduction", "What happens to electrons in oxidation?", "Oxidation gains electrons.", False, "REDOX_ELECTRON_DIRECTION", 0.86),
    ("Vivaan Singh", "Writing Chemical Equations", "Write magnesium oxide formation.", "MgO -> Mg + O2", False, "EQN_REACTANT_PRODUCT_SWAP", 0.78),
    ("Tara Menon", "Types of Chemical Reactions", "Identify CaCO3 -> CaO + CO2.", "Combination reaction.", False, "RXN_TYPE_COMB_DECOMP_SWAP", 0.8),
    ("Aarav Mehta", "Acid and Base Indicators", "What happens to blue litmus in acid?", "It stays blue.", False, "INDICATOR_COLOR_REVERSAL", 0.77),
    ("Diya Shah", "Water of Crystallisation", "What is water of crystallisation?", "Water stuck on the outside of crystals.", False, "CRYSTAL_WATER_FREE_WATER", 0.83),
    ("Kabir Nair", "Extraction of Metals", "Why use electrolysis for sodium?", "Because sodium is low in reactivity.", False, "EXTRACTION_REACTIVITY_IGNORED", 0.8),
    ("Anika Rao", "Corrosion Prevention", "How does galvanising protect iron?", "It is just paint on iron.", False, "GALVANISING_PAINTING_SWAP", 0.81),
    ("Ishaan Iyer", "Physical Properties of Metals", "What is malleability?", "It means metal can be drawn into wires.", False, "DUCTILE_MALLEABLE_SWAP", 0.79),
    ("Meera Kulkarni", "Salts and Their Preparation", "Which ions form copper sulphate?", "Copper and sodium ions.", False, "SALT_SOURCE_ION_ERROR", 0.76),
    ("Rohan Das", "Corrosion and Rancidity", "What causes rancidity?", "Bacteria only, not oxidation.", False, "RANCIDITY_MICROBE_CONFUSION", 0.74),
    ("Sara Khan", "Reactivity Series", "Can magnesium displace zinc?", "Yes, magnesium is above zinc.", True, None, 0.93),
    ("Vivaan Singh", "Balancing Chemical Equations", "Balance 2H2 + O2 -> 2H2O.", "It has 4 H and 2 O on both sides.", True, None, 0.95),
    ("Tara Menon", "Acid and Base Indicators", "What does red litmus do in base?", "It turns blue.", True, None, 0.94),
)


def get_or_create(session: Session, model: type, defaults: dict[str, object] | None = None, **filters: object):
    instance = session.scalar(select(model).filter_by(**filters))
    if instance:
        return instance
    instance = model(**filters, **(defaults or {}))
    session.add(instance)
    session.flush()
    return instance


def seed(session: Session) -> None:
    if session.scalar(select(func.count(Subject.id)).where(Subject.name == "CBSE Class 10 Science")):
        print("Seed data already present; leaving existing rows unchanged.")
        return

    now = datetime.now(UTC)

    subject = get_or_create(
        session,
        Subject,
        name="CBSE Class 10 Science",
        board="CBSE",
        class_level="10",
    )
    teacher = get_or_create(session, Teacher, name="Nisha Verma")
    classroom = get_or_create(
        session,
        Classroom,
        teacher_id=teacher.id,
        subject_id=subject.id,
        name="Class 10A Science",
    )

    chapters: dict[str, Chapter] = {}
    for title, order in CHAPTERS:
        chapters[title] = get_or_create(session, Chapter, subject_id=subject.id, title=title, order=order)

    concepts: dict[str, Concept] = {}
    for seed_concept in CONCEPTS:
        concept = get_or_create(
            session,
            Concept,
            chapter_id=chapters[seed_concept.chapter].id,
            title=seed_concept.title,
            order=seed_concept.order,
        )
        concepts[seed_concept.title] = concept
        for code, description in seed_concept.misconceptions:
            get_or_create(session, MisconceptionTaxonomy, concept_id=concept.id, code=code, defaults={"description": description})

    for concept_title, prerequisite_title, weight in EDGES:
        get_or_create(
            session,
            ConceptEdge,
            concept_id=concepts[concept_title].id,
            prerequisite_concept_id=concepts[prerequisite_title].id,
            defaults={"weight": weight},
        )

    students: dict[str, Student] = {}
    for name in STUDENT_NAMES:
        student = get_or_create(session, Student, name=name)
        students[name] = student
        get_or_create(session, ClassroomStudent, classroom_id=classroom.id, student_id=student.id)

    first_chapter = chapters["Chemical Reactions and Equations"]
    get_or_create(session, ChapterUnlock, classroom_id=classroom.id, chapter_id=first_chapter.id, defaults={"unlocked_by": teacher.id})

    review_offsets = (2, 5, 8, 11, 15, 18, 22, 25, 29, 32)
    for student_index, student in enumerate(students.values()):
        for concept_index, concept in enumerate(concepts.values()):
            base = max(0.42, min(0.92, 0.88 - (student_index * 0.035) - ((concept_index % 5) * 0.025)))
            recurrence = max(0.05, min(0.65, 0.18 + (student_index % 4) * 0.08 + (concept_index % 3) * 0.04))
            retention = max(0.38, min(0.9, base - (review_offsets[student_index] * 0.006)))
            mastery = compute_mastery(base, max(0.4, base - 0.08), recurrence, retention)
            reviewed_at = now - timedelta(days=review_offsets[student_index] + (concept_index % 4))
            get_or_create(
                session,
                MasteryRecord,
                student_id=student.id,
                concept_id=concept.id,
                defaults={
                    "quiz_accuracy_score": round(base, 3),
                    "open_answer_score": round(max(0.4, base - 0.08), 3),
                    "misconception_recurrence": round(recurrence, 3),
                    "retention_score": round(retention, 3),
                    "computed_mastery": mastery,
                    "last_reviewed_at": reviewed_at,
                    "next_review_date": (reviewed_at + timedelta(days=14)).date(),
                },
            )

    for student_name, concept_title, question, answer, is_correct, code, confidence in QUIZ_ATTEMPTS:
        session.add(
            QuizAttempt(
                student_id=students[student_name].id,
                concept_id=concepts[concept_title].id,
                question=question,
                student_answer=answer,
                is_correct=is_correct,
                misconception_code=code,
                confidence=confidence,
                mode="quiz",
            )
        )

    session.commit()


def backfill_mastery_history(session: Session, weeks: int = 6) -> int:
    """Add a weekly mastery snapshot series per (student, concept), trending up to
    the current computed_mastery. Idempotent — safe to run against an already-seeded
    DB (it only inserts points that don't already exist). Powers the mastery-over-time
    chart on the student Progress screen; the values are synthetic demo history.
    """
    today = datetime.now(UTC).date()
    # Keep the synthetic timeline anchored to the same weekly snapshots on every seed run.
    reference = today - timedelta(days=today.weekday())
    records = session.scalars(select(MasteryRecord)).all()
    created = 0
    for record in records:
        final = record.computed_mastery
        start = round(max(0.0, final * 0.5), 4)
        for week in range(weeks, -1, -1):
            recorded_at = reference - timedelta(weeks=week)
            progress = (weeks - week) / weeks
            wiggle = ((record.concept_id + week) % 3 - 1) * 0.015
            value = round(min(1.0, max(0.0, start + (final - start) * progress + wiggle)), 4)
            exists = session.scalar(
                select(MasteryHistory.id).where(
                    MasteryHistory.student_id == record.student_id,
                    MasteryHistory.concept_id == record.concept_id,
                    MasteryHistory.recorded_at == recorded_at,
                )
            )
            if exists:
                continue
            session.add(
                MasteryHistory(
                    student_id=record.student_id,
                    concept_id=record.concept_id,
                    mastery=value,
                    recorded_at=recorded_at,
                )
            )
            created += 1
    session.commit()
    return created


# All plans are priced at $0 for now; they differ by enabled modules + limits.
PLANS = (
    ("individual_free", "individual", "Individual — Free", {"max_students": 1, "max_classrooms": 1, "ai_calls_per_day": 50}, ["learning"]),
    ("institute_free", "institute", "Institute — Free", {"max_students": 200, "max_classrooms": 20, "ai_calls_per_day": 50}, ["learning"]),
    ("institute_plus_free", "institute", "Institute Plus — Free", {"max_students": 500, "max_classrooms": 50, "ai_calls_per_day": 50}, ["learning", "fees"]),
    ("school_free", "school", "School — Free", {"max_students": 5000, "max_classrooms": 500, "ai_calls_per_day": 50}, ["learning", "curriculum", "admissions", "accounting", "hr", "parent"]),
)

DEMO_ORG_SLUG = "confusionlayer-demo"
INSTITUTE_DEMO_ORG_SLUG = "slate-demo-institute"
INDIVIDUAL_DEMO_ORG_SLUG = "slate-demo-individual"
DEMO_PASSWORD = "password123"


def _demo_hash() -> str:
    return hash_password(DEMO_PASSWORD)


def _ensure_user(
    session: Session,
    *,
    email: str,
    name: str,
    role: str,
    org_id: int | None,
    department: str,
    teacher_id: int | None = None,
    student_id: int | None = None,
) -> User:
    user = session.scalar(select(User).where(User.email == email))
    if user:
        user.name = name
        user.role = role
        user.org_id = org_id
        user.department = department
        user.teacher_id = teacher_id
        user.student_id = student_id
        user.status = "active"
        return user
    user = User(
        email=email,
        name=name,
        password_hash=_demo_hash(),
        role=role,
        org_id=org_id,
        department=department,
        teacher_id=teacher_id,
        student_id=student_id,
        email_verified=True,
    )
    session.add(user)
    session.flush()
    return user


def _ensure_curriculum(session: Session, *, org_id: int, name: str) -> tuple[Subject, dict[str, Chapter], dict[str, Concept]]:
    subject = get_or_create(session, Subject, name=name, board="CBSE", class_level="10", defaults={"org_id": org_id})
    subject.org_id = org_id

    chapters: dict[str, Chapter] = {}
    for title, order in CHAPTERS:
        chapters[title] = get_or_create(session, Chapter, subject_id=subject.id, title=title, order=order)

    concepts: dict[str, Concept] = {}
    for seed_concept in CONCEPTS:
        concept = get_or_create(
            session,
            Concept,
            chapter_id=chapters[seed_concept.chapter].id,
            title=seed_concept.title,
            order=seed_concept.order,
        )
        concepts[seed_concept.title] = concept
        for code, description in seed_concept.misconceptions:
            get_or_create(session, MisconceptionTaxonomy, concept_id=concept.id, code=code, defaults={"description": description})

    for concept_title, prerequisite_title, weight in EDGES:
        get_or_create(
            session,
            ConceptEdge,
            concept_id=concepts[concept_title].id,
            prerequisite_concept_id=concepts[prerequisite_title].id,
            defaults={"weight": weight},
        )
    return subject, chapters, concepts


def _seed_learning_records(
    session: Session,
    *,
    classroom: Classroom,
    students: list[Student],
    concepts: dict[str, Concept],
    now: datetime,
    stronger_offset: float = 0.0,
) -> None:
    concept_list = list(concepts.values())
    for student_index, student in enumerate(students):
        for concept_index, concept in enumerate(concept_list):
            base = max(0.38, min(0.95, 0.86 + stronger_offset - (student_index * 0.03) - ((concept_index % 5) * 0.025)))
            recurrence = max(0.04, min(0.72, 0.16 + (student_index % 4) * 0.08 + (concept_index % 3) * 0.045))
            reviewed_at = now - timedelta(days=3 + student_index * 2 + (concept_index % 4))
            retention = max(0.35, min(0.92, base - ((now - reviewed_at).days * 0.005)))
            mastery = compute_mastery(base, max(0.35, base - 0.08), recurrence, retention)
            record = session.scalar(select(MasteryRecord).where(MasteryRecord.student_id == student.id, MasteryRecord.concept_id == concept.id))
            if not record:
                session.add(
                    MasteryRecord(
                        student_id=student.id,
                        concept_id=concept.id,
                        quiz_accuracy_score=round(base, 3),
                        open_answer_score=round(max(0.35, base - 0.08), 3),
                        misconception_recurrence=round(recurrence, 3),
                        retention_score=round(retention, 3),
                        computed_mastery=mastery,
                        last_reviewed_at=reviewed_at,
                        next_review_date=(reviewed_at + timedelta(days=14)).date(),
                    )
                )

    target_concepts = [concepts["Reactivity Series"], concepts["Ionic Bonding"], concepts["Neutralisation Reactions"]]
    for student_index, student in enumerate(students[: min(8, len(students))]):
        concept = target_concepts[student_index % len(target_concepts)]
        code = {
            "Reactivity Series": "RXN_ELECTRONEGATIVITY_CONFUSION",
            "Ionic Bonding": "IONIC_SHARE_CONFUSION",
            "Neutralisation Reactions": "NEUTRAL_WATER_MISSING",
        }[concept.title]
        session.add(
            QuizAttempt(
                student_id=student.id,
                concept_id=concept.id,
                question=f"Explain {concept.title} in one example.",
                student_answer="I mixed the rule with a similar idea and missed the key condition.",
                is_correct=False,
                misconception_code=code,
                confidence=round(0.74 + (student_index % 4) * 0.04, 2),
                mode="quiz",
            )
        )
        session.add(
            TeachBackAttempt(
                student_id=student.id,
                concept_id=concept.id,
                student_explanation=f"{concept.title} works because the stronger idea always replaces the weaker one.",
                clarity_score=0.62,
                accuracy_score=0.54,
                gpt_feedback="Good structure, but the explanation needs the actual science rule and one correct example.",
            )
        )

    for student in students:
        for concept in target_concepts:
            existing = session.scalar(select(ForecastRecord.id).where(ForecastRecord.student_id == student.id, ForecastRecord.concept_id == concept.id))
            if existing:
                continue
            session.add(
                ForecastRecord(
                    student_id=student.id,
                    concept_id=concept.id,
                    predicted_difficulty=0.58 + ((student.id + concept.id) % 5) * 0.07,
                    contributing_concepts=[
                        {"concept_id": concept.id, "title": concept.title, "effective_mastery": 0.46, "contribution_weight": 0.8, "difficulty_component": 0.43, "distance": 1}
                    ],
                    computed_at=now,
                )
            )

    first_chapter = classroom.subject.chapters[0] if classroom.subject.chapters else None
    if first_chapter:
        get_or_create(session, ChapterUnlock, classroom_id=classroom.id, chapter_id=first_chapter.id, defaults={"unlocked_by": classroom.teacher_id})


def _seed_school_operations(session: Session, org: Organization, users: dict[str, User], classroom: Classroom, students: list[Student]) -> None:
    today = datetime.now(UTC).date()
    for name, amount in (("Term 1 tuition", 2800000), ("Science lab fee", 450000), ("Transport term pass", 900000)):
        get_or_create(session, FeeStructure, org_id=org.id, name=name, defaults={"amount_cents": amount})

    for index, student in enumerate(students[:6]):
        invoice = get_or_create(
            session,
            Invoice,
            org_id=org.id,
            student_id=student.id,
            recipient_name=student.name,
            description="Term 1 tuition and activity charges",
            defaults={"amount_cents": 2800000 + (index % 3) * 150000, "due_date": today + timedelta(days=10 + index)},
        )
        if not session.scalar(select(InvoiceLineItem.id).where(InvoiceLineItem.invoice_id == invoice.id)):
            session.add(InvoiceLineItem(invoice_id=invoice.id, description="Tuition", amount_cents=2400000 + (index % 3) * 150000))
            session.add(InvoiceLineItem(invoice_id=invoice.id, description="Activities", amount_cents=400000))
        if index in (0, 1, 3) and not session.scalar(select(Payment.id).where(Payment.invoice_id == invoice.id)):
            session.add(Payment(org_id=org.id, invoice_id=invoice.id, amount_cents=min(invoice.amount_cents, 1800000 + index * 250000), method="upi", note="Demo payment"))

    application_rows = (
        ("Riya Bansal", "riya.parent@example.com", "Class 10", "Website", "applied"),
        ("Dev Malhotra", "dev.parent@example.com", "Class 10", "Walk-in", "reviewing"),
        ("Ayaan Joseph", "ayaan.parent@example.com", "Class 9", "Referral", "accepted"),
        ("Naina Bose", "naina.parent@example.com", "Class 10", "Open house", "enrolled"),
    )
    for name, email, grade, source, status_value in application_rows:
        get_or_create(
            session,
            AdmissionApplication,
            org_id=org.id,
            applicant_name=name,
            defaults={"applicant_email": email, "grade": grade, "source": source, "status": status_value, "notes": "Seeded demo enquiry"},
        )

    designations = {
        "Science Teacher": get_or_create(session, Designation, org_id=org.id, name="Science Teacher", defaults={"department": "Teaching & learning"}),
        "Accounts Executive": get_or_create(session, Designation, org_id=org.id, name="Accounts Executive", defaults={"department": "Accounts"}),
        "HR Coordinator": get_or_create(session, Designation, org_id=org.id, name="HR Coordinator", defaults={"department": "HR"}),
        "Admissions Counselor": get_or_create(session, Designation, org_id=org.id, name="Admissions Counselor", defaults={"department": "Admissions"}),
    }
    salary = get_or_create(session, SalaryStructure, org_id=org.id, name="Monthly full-time", defaults={"monthly_amount_cents": 5200000})
    staff = (
        ("Nisha Verma", "nisha@slate.demo", "Science Teacher", 6200000),
        ("Karan Mehta", "karan@slate.demo", "Accounts Executive", 4300000),
        ("Pooja Rao", "pooja@slate.demo", "HR Coordinator", 4100000),
        ("Sameer Khan", "sameer@slate.demo", "Admissions Counselor", 3900000),
    )
    employees: list[Employee] = []
    for name, email, designation_name, salary_cents in staff:
        employee = get_or_create(
            session,
            Employee,
            org_id=org.id,
            email=email,
            defaults={
                "name": name,
                "designation": designation_name,
                "designation_id": designations[designation_name].id,
                "salary_structure_id": salary.id,
                "salary_cents": salary_cents,
                "phone": "9000000000",
                "join_date": date(2025, 6, 1),
                "status": "active",
            },
        )
        employees.append(employee)

    run = get_or_create(session, PayrollRun, org_id=org.id, period="2026-07", defaults={"status": "finalized"})
    for employee in employees:
        if not session.scalar(select(Payslip.id).where(Payslip.payroll_run_id == run.id, Payslip.employee_name == employee.name)):
            session.add(Payslip(org_id=org.id, payroll_run_id=run.id, employee_id=employee.id, employee_name=employee.name, gross_cents=employee.salary_cents, net_cents=int(employee.salary_cents * 0.92)))

    weekdays = [(0, "09:00", "09:45"), (1, "10:00", "10:45"), (2, "11:00", "11:45"), (3, "09:00", "09:45"), (4, "12:00", "12:45")]
    for weekday, starts_at, ends_at in weekdays:
        get_or_create(session, TimetableEntry, org_id=org.id, classroom_id=classroom.id, weekday=weekday, starts_at=starts_at, defaults={"ends_at": ends_at, "room": "Science Lab 2"})

    statuses = ("present", "present", "present", "late", "absent")
    for day_offset in range(8):
        school_day = today - timedelta(days=day_offset)
        if school_day.weekday() >= 5:
            continue
        for index, student in enumerate(students):
            get_or_create(
                session,
                AttendanceRecord,
                org_id=org.id,
                classroom_id=classroom.id,
                student_id=student.id,
                attendance_date=school_day,
                defaults={"status": statuses[(index + day_offset) % len(statuses)], "recorded_by": users["teacher"].id},
            )

    if students:
        get_or_create(session, GuardianLink, org_id=org.id, parent_user_id=users["parent"].id, student_id=students[0].id)

    for user_key, title, body, href in (
        ("owner", "Admissions funnel needs review", "Two accepted applicants are ready for enrollment.", "/app/admissions"),
        ("teacher", "Tomorrow's forecast is ready", "Reactivity Series has the highest predicted difficulty.", "/app/teacher/forecast"),
        ("accountant", "Fee follow-up", "Three term invoices still have outstanding balances.", "/app/fees"),
        ("hr", "Payroll finalized", "July payroll is ready for review.", "/app/hr"),
    ):
        get_or_create(session, Notification, user_id=users[user_key].id, title=title, defaults={"body": body, "href": href})

    for action, target, actor in (
        ("demo.seed.reset", "Production demo data", users["owner"]),
        ("fees.payment.recorded", "Term fee payment", users["accountant"]),
        ("hr.payroll.finalized", "Payroll 2026-07", users["hr"]),
    ):
        session.add(AuditLog(org_id=org.id, actor_user_id=actor.id, action=action, target=target, audit_metadata={"source": "seed"}))


def seed_demo_showcase(session: Session) -> dict[str, int]:
    now = datetime.now(UTC)
    for code, segment, name, limits, features in PLANS:
        get_or_create(session, Plan, code=code, defaults={"segment": segment, "name": name, "price_cents": 0, "limits": limits, "features": features})

    school = get_or_create(session, Organization, slug=DEMO_ORG_SLUG, defaults={"name": "Slate Demo School", "segment": "school"})
    school.name = "Slate Demo School"
    school.segment = "school"
    institute = get_or_create(session, Organization, slug=INSTITUTE_DEMO_ORG_SLUG, defaults={"name": "Slate Demo Institute", "segment": "institute"})
    individual = get_or_create(session, Organization, slug=INDIVIDUAL_DEMO_ORG_SLUG, defaults={"name": "Slate Individual Learner", "segment": "individual"})
    for org, plan_code in ((school, "school_free"), (institute, "institute_free"), (individual, "individual_free")):
        plan = session.scalar(select(Plan).where(Plan.code == plan_code))
        subscription = get_or_create(session, Subscription, org_id=org.id, defaults={"plan_id": plan.id, "status": "active"})
        subscription.plan_id = plan.id
        subscription.status = "active"

    school_subject, _, school_concepts = _ensure_curriculum(session, org_id=school.id, name="CBSE Class 10 Science")
    institute_subject, _, institute_concepts = _ensure_curriculum(session, org_id=institute.id, name="CBSE Class 10 Science - Institute Demo")
    individual_subject, _, individual_concepts = _ensure_curriculum(session, org_id=individual.id, name="CBSE Class 10 Science - Self Study")

    _ensure_user(session, email="demo.platform.platform_admin@confusionlayer.local", name="Platform Admin", role="platform_admin", org_id=None, department="Platform")

    school_teacher = get_or_create(session, Teacher, name="Nisha Verma")
    school_classroom = get_or_create(session, Classroom, org_id=school.id, name="Class 10A Science", defaults={"teacher_id": school_teacher.id, "subject_id": school_subject.id})
    school_classroom.teacher_id = school_teacher.id
    school_classroom.subject_id = school_subject.id
    school_users = {
        "owner": _ensure_user(session, email="demo.school.owner@confusionlayer.local", name="Anaya Kapoor", role="owner", org_id=school.id, department="School leadership"),
        "school_admin": _ensure_user(session, email="demo.school.school_admin@confusionlayer.local", name="Ritika Sharma", role="school_admin", org_id=school.id, department="Front-office"),
        "accountant": _ensure_user(session, email="demo.school.accountant@confusionlayer.local", name="Karan Mehta", role="accountant", org_id=school.id, department="Accounts"),
        "hr": _ensure_user(session, email="demo.school.hr@confusionlayer.local", name="Pooja Rao", role="hr", org_id=school.id, department="HR"),
        "teacher": _ensure_user(session, email="demo.school.teacher@confusionlayer.local", name="Nisha Verma", role="teacher", org_id=school.id, department="Teaching & learning", teacher_id=school_teacher.id),
    }
    school_students: list[Student] = []
    for index, name in enumerate(STUDENT_NAMES, start=1):
        student = get_or_create(session, Student, name=name, defaults={"roll_number": f"10A-{index:02d}", "section": "10A", "guardian_name": "Demo Guardian", "guardian_phone": "9000000000"})
        school_students.append(student)
        get_or_create(session, ClassroomStudent, classroom_id=school_classroom.id, student_id=student.id)
        if index <= 4:
            _ensure_user(session, email=f"demo.school.student{index}@confusionlayer.local", name=name, role="student", org_id=school.id, department="Learning", student_id=student.id)
    school_users["student"] = _ensure_user(session, email="demo.school.student@confusionlayer.local", name=school_students[0].name, role="student", org_id=school.id, department="Learning", student_id=school_students[0].id)
    school_users["parent"] = _ensure_user(session, email="demo.school.parent@confusionlayer.local", name="Meera Mehta", role="parent", org_id=school.id, department="Family")
    _seed_learning_records(session, classroom=school_classroom, students=school_students, concepts=school_concepts, now=now)
    _seed_school_operations(session, school, school_users, school_classroom, school_students)

    institute_teacher = get_or_create(session, Teacher, name="Arjun Sen")
    institute_classroom = get_or_create(session, Classroom, org_id=institute.id, name="Evening Class 10 Science", defaults={"teacher_id": institute_teacher.id, "subject_id": institute_subject.id})
    institute_classroom.teacher_id = institute_teacher.id
    institute_classroom.subject_id = institute_subject.id
    _ensure_user(session, email="demo.institute.owner@confusionlayer.local", name="Maya Iyer", role="owner", org_id=institute.id, department="School leadership")
    _ensure_user(session, email="demo.institute.teacher@confusionlayer.local", name="Arjun Sen", role="teacher", org_id=institute.id, department="Teaching & learning", teacher_id=institute_teacher.id)
    institute_students: list[Student] = []
    for index, name in enumerate(("Neil Sethi", "Aditi Roy", "Pranav Jain", "Kiara Thomas", "Zoya Ali"), start=1):
        student = get_or_create(session, Student, name=name, defaults={"roll_number": f"INS-{index:02d}", "section": "Batch B"})
        institute_students.append(student)
        get_or_create(session, ClassroomStudent, classroom_id=institute_classroom.id, student_id=student.id)
        _ensure_user(session, email=f"demo.institute.student{index}@confusionlayer.local", name=name, role="student", org_id=institute.id, department="Learning", student_id=student.id)
    _seed_learning_records(session, classroom=institute_classroom, students=institute_students, concepts=institute_concepts, now=now, stronger_offset=0.04)

    individual_teacher = get_or_create(session, Teacher, name="Self Study Coach")
    individual_student = get_or_create(session, Student, name="Ira Self Study", defaults={"roll_number": "SELF-01", "section": "Self"})
    individual_classroom = get_or_create(session, Classroom, org_id=individual.id, name="My Science Plan", defaults={"teacher_id": individual_teacher.id, "subject_id": individual_subject.id})
    individual_classroom.teacher_id = individual_teacher.id
    individual_classroom.subject_id = individual_subject.id
    get_or_create(session, ClassroomStudent, classroom_id=individual_classroom.id, student_id=individual_student.id)
    _ensure_user(session, email="demo.individual.student@confusionlayer.local", name=individual_student.name, role="student", org_id=individual.id, department="Learning", student_id=individual_student.id)
    _seed_learning_records(session, classroom=individual_classroom, students=[individual_student], concepts=individual_concepts, now=now, stronger_offset=0.1)

    session.commit()
    return {
        "orgs": int(session.scalar(select(func.count(Organization.id))) or 0),
        "users": int(session.scalar(select(func.count(User.id))) or 0),
        "students": int(session.scalar(select(func.count(Student.id))) or 0),
    }


def reset_database() -> None:
    if os.getenv("CONFUSIONLAYER_ALLOW_DB_RESET") != "1":
        raise RuntimeError("Set CONFUSIONLAYER_ALLOW_DB_RESET=1 to clear and rebuild the database.")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def backfill_tenancy(session: Session) -> dict[str, int]:
    """Idempotently ensure plans, the demo organization, its subscription, and that
    existing classrooms/users belong to an org. Safe to run against a live DB.
    """
    for code, segment, name, limits, features in PLANS:
        get_or_create(session, Plan, code=code, defaults={"segment": segment, "name": name, "price_cents": 0, "limits": limits, "features": features})

    org = get_or_create(session, Organization, slug=DEMO_ORG_SLUG, defaults={"name": "Slate Demo School", "segment": "school"})
    school_plan = session.scalar(select(Plan).where(Plan.code == "school_free"))
    get_or_create(session, Subscription, org_id=org.id, defaults={"plan_id": school_plan.id, "status": "active"})

    attached_classrooms = 0
    for classroom in session.scalars(select(Classroom).where(Classroom.org_id.is_(None))).all():
        classroom.org_id = org.id
        attached_classrooms += 1

    attached_users = 0
    for user in session.scalars(select(User).where(User.org_id.is_(None), User.role != "platform_admin")).all():
        user.org_id = org.id
        attached_users += 1

    session.commit()
    return {"classrooms": attached_classrooms, "users": attached_users}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Slate demo data.")
    parser.add_argument("--reset-demo", action="store_true", help="Clear all tables, recreate schema, and load the full demo dataset.")
    args = parser.parse_args()

    if args.reset_demo:
        reset_database()

    with SessionLocal() as session:
        seed(session)
        tenancy = backfill_tenancy(session)
        created = backfill_mastery_history(session)
        showcase = seed_demo_showcase(session)
        created += backfill_mastery_history(session)
    print(
        f"Seed data ready. Tenancy backfill: {tenancy['classrooms']} classrooms, "
        f"{tenancy['users']} users attached to the demo org. Mastery history points added: {created}. "
        f"Demo showcase: {showcase['orgs']} orgs, {showcase['users']} users, {showcase['students']} students."
    )


if __name__ == "__main__":
    main()
