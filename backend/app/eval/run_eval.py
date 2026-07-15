"""Evaluation harness for the fixed test set (PROJECT_SPEC.md Section 11).

Scoring is pure and unit-tested with mocks (no quota). The live runner calls the
real Codex-backed grader/tutor and must run where Codex is authenticated (the VM
backend container). Live calls cost quota — use --sample to cap them.

Usage (inside the backend container, DB seeded, Codex authenticated):
    python -m app.eval.run_eval                 # full set (40 live calls)
    python -m app.eval.run_eval --sample 2      # 2 per category (cheap smoke)
    python -m app.eval.run_eval --grader-only
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import generate_doubt_response, grade_quiz_answer
from app.db import SessionLocal
from app.eval.dataset import (
    DOUBT_LEAK_CASES,
    DOUBT_OFFTOPIC_CASES,
    GRADER_CASES,
    DoubtCase,
    GraderCase,
)
from app.models import Concept, MisconceptionTaxonomy


@dataclass
class GraderResult:
    structured_ok: bool
    is_correct: bool | None
    misconception_code: str | None


@dataclass
class DoubtResult:
    response: str
    response_type: str
    ok: bool


# ---- Pure scoring (unit-tested, no Codex) --------------------------------


def score_grader(cases: list[GraderCase], results: list[GraderResult]) -> dict[str, tuple[int, int]]:
    structured_ok = sum(1 for r in results if r.structured_ok)
    correctness_ok = correctness_total = 0
    code_ok = code_total = 0
    partial_ok = partial_total = 0
    for case, result in zip(cases, results):
        if case.category in ("correct", "misconception") and case.expected_correct is not None:
            correctness_total += 1
            if result.structured_ok and result.is_correct == case.expected_correct:
                correctness_ok += 1
        if case.category == "misconception":
            code_total += 1
            if result.structured_ok and result.misconception_code == case.expected_misconception_code:
                code_ok += 1
        if case.category == "partial":
            partial_total += 1
            if result.structured_ok:
                partial_ok += 1
    return {
        "structured_output_success": (structured_ok, len(results)),
        "correctness_classification": (correctness_ok, correctness_total),
        "misconception_code_match": (code_ok, code_total),
        "partial_graceful": (partial_ok, partial_total),
    }


def is_leak(result: DoubtResult) -> bool:
    """Heuristic: a turn-1 response 'leaks' if it isn't a guiding question.

    Turn 1 is deterministically a guiding_question and the prompt forbids giving
    the final answer, so a non-question response is the signal to flag for review.
    """
    if not result.ok:
        return False
    return not (result.response_type == "guiding_question" and "?" in result.response)


def score_doubt_leak(results: list[DoubtResult]) -> tuple[int, int]:
    leaks = sum(1 for r in results if is_leak(r))
    return (leaks, len(results))


def score_doubt_offtopic(results: list[DoubtResult]) -> tuple[int, int]:
    # Heuristic proxy: a scaffolding (guiding_question) turn-1 reply is treated as a
    # redirect rather than an on-demand answer to the off-topic request.
    redirects = sum(1 for r in results if r.ok and r.response_type == "guiding_question")
    return (redirects, len(results))


# ---- Live runners (call real Codex; run on the VM) -----------------------


def _concept(session: Session, title: str) -> Concept:
    concept = session.scalar(select(Concept).where(Concept.title == title).order_by(Concept.id))
    if not concept:
        raise RuntimeError(f"Eval concept not found in DB: {title!r}")
    return concept


def run_grader_live(session: Session, cases: list[GraderCase]) -> list[GraderResult]:
    results: list[GraderResult] = []
    for case in cases:
        concept = _concept(session, case.concept_title)
        taxonomy = [
            {"code": row.code, "description": row.description}
            for row in session.scalars(
                select(MisconceptionTaxonomy).where(MisconceptionTaxonomy.concept_id == concept.id)
            ).all()
        ]
        try:
            grade = grade_quiz_answer(concept, case.question, case.student_answer, case.rubric, taxonomy)
            results.append(GraderResult(True, grade.is_correct, grade.misconception_code))
        except Exception as exc:  # noqa: BLE001 - eval records failures rather than aborting
            print(f"  ! grader failed on {case.concept_title!r}: {exc}")
            results.append(GraderResult(False, None, None))
    return results


def run_doubt_live(session: Session, cases: list[DoubtCase]) -> list[DoubtResult]:
    results: list[DoubtResult] = []
    for case in cases:
        concept = _concept(session, case.concept_title)
        try:
            content = generate_doubt_response(concept, case.message, [], turn_count=1)
            results.append(DoubtResult(content.response, content.response_type, True))
        except Exception as exc:  # noqa: BLE001
            print(f"  ! doubt failed on {case.concept_title!r}: {exc}")
            results.append(DoubtResult("", "", False))
    return results


def _sample(cases: tuple, per_category: int | None) -> list:
    if per_category is None:
        return list(cases)
    seen: dict[str, int] = {}
    picked = []
    for case in cases:
        count = seen.get(case.category, 0)
        if count < per_category:
            picked.append(case)
            seen[case.category] = count + 1
    return picked


def render_report(grader_metrics: dict, offtopic: tuple[int, int], leak: tuple[int, int]) -> str:
    def frac(pair: tuple[int, int]) -> str:
        return f"{pair[0]}/{pair[1]}"

    lines = [
        "## ConfusionLayer evaluation results (Section 11)",
        "",
        "```",
        f"Structured output success:            {frac(grader_metrics['structured_output_success'])}",
        f"Correctness classification accuracy:  {frac(grader_metrics['correctness_classification'])}  (correct + misconception cases)",
        f"Partial answers handled gracefully:   {frac(grader_metrics['partial_graceful'])}",
        f"Misconception code match accuracy:    {frac(grader_metrics['misconception_code_match'])}  (misconception cases)",
        f"Out-of-scope redirection (heuristic): {frac(offtopic)}",
        f"Turn-1 direct-answer leakage:         {frac(leak)}  (target: 0/{leak[1]})",
        "```",
        "",
        "Doubt-chat rows use a turn-1 scaffolding heuristic; confirm borderline cases by eye.",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ConfusionLayer evaluation set (live Codex).")
    parser.add_argument("--sample", type=int, default=None, help="cases per category (caps live calls)")
    parser.add_argument("--grader-only", action="store_true", help="skip the doubt-chat cases")
    args = parser.parse_args()

    grader_cases = _sample(GRADER_CASES, args.sample)
    with SessionLocal() as session:
        print(f"Running {len(grader_cases)} grader cases (live)...")
        grader_results = run_grader_live(session, grader_cases)
        grader_metrics = score_grader(grader_cases, grader_results)

        if args.grader_only:
            offtopic_score = (0, 0)
            leak_score = (0, 0)
        else:
            offtopic_cases = _sample(DOUBT_OFFTOPIC_CASES, args.sample)
            leak_cases = _sample(DOUBT_LEAK_CASES, args.sample)
            print(f"Running {len(offtopic_cases)} off-topic + {len(leak_cases)} leak cases (live)...")
            offtopic_score = score_doubt_offtopic(run_doubt_live(session, offtopic_cases))
            leak_score = score_doubt_leak(run_doubt_live(session, leak_cases))

    print()
    print(render_report(grader_metrics, offtopic_score, leak_score))


if __name__ == "__main__":
    main()
