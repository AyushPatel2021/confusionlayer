from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.mastery import compute_mastery
from app.models import (
    Chapter,
    ChapterUnlock,
    Classroom,
    ClassroomStudent,
    Concept,
    ConceptEdge,
    MasteryHistory,
    MasteryRecord,
    MisconceptionTaxonomy,
    QuizAttempt,
    Student,
    Subject,
    Teacher,
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
    reference = datetime.now(UTC).date()
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


def main() -> None:
    with SessionLocal() as session:
        seed(session)
        created = backfill_mastery_history(session)
    print(f"Seed data ready. Mastery history points added: {created}.")


if __name__ == "__main__":
    main()
