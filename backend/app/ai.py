from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AiCallUsage, Concept, User


@dataclass(frozen=True)
class TutorialContent:
    explanation: str
    analogy: str
    worked_example: str
    visual: str


@dataclass(frozen=True)
class DoubtChatContent:
    response: str
    response_type: str


@dataclass(frozen=True)
class QuizGradeContent:
    is_correct: bool
    misconception_code: str | None
    misconception_summary: str
    confidence: float
    follow_up_question: str


@dataclass(frozen=True)
class TeachBackGradeContent:
    clarity_score: float
    accuracy_score: float
    gap_identified: str
    encouragement: str


@dataclass(frozen=True)
class BriefNarrativeContent:
    summary: str
    suggested_activity: str


@dataclass(frozen=True)
class CurriculumDraftContent:
    chapters: list[dict[str, Any]]


def ai_daily_call_limit() -> int:
    return int(os.getenv("AI_DAILY_CALL_LIMIT", "50"))


def codex_model() -> str:
    return os.getenv("CODEX_MODEL", "gpt-5.6-luna")


def codex_timeout_seconds() -> int:
    return int(os.getenv("CODEX_TIMEOUT_SECONDS", "90"))


def check_and_increment_ai_usage(db: Session, user: User, usage_date: date | None = None) -> AiCallUsage:
    today = usage_date or datetime.now(UTC).date()
    limit = ai_daily_call_limit()
    usage = db.scalar(select(AiCallUsage).where(AiCallUsage.user_id == user.id, AiCallUsage.usage_date == today))
    if not usage:
        usage = AiCallUsage(user_id=user.id, usage_date=today, call_count=0)
        db.add(usage)
        db.flush()

    if usage.call_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily AI call limit reached ({limit}/day)",
        )

    usage.call_count += 1
    db.commit()
    db.refresh(usage)
    return usage


def generate_tutorial(concept: Concept, reading_level: str) -> TutorialContent:
    prompt = f"{_tutorial_instructions()}\n\n{_tutorial_input(concept, reading_level)}"
    response_text = _run_codex_json(prompt, "tutorial.schema.json")
    return parse_tutorial_response(response_text)


def generate_self_start_tutorial(topic: str, reading_level: str, subject_context: dict[str, str]) -> TutorialContent:
    prompt = f"{_self_start_instructions()}\n\n{_self_start_input(topic, reading_level, subject_context)}"
    response_text = _run_codex_json(prompt, "tutorial.schema.json")
    return parse_tutorial_response(response_text)


def generate_doubt_response(concept: Concept, message: str, history: list[dict[str, str]], turn_count: int) -> DoubtChatContent:
    response_type = doubt_response_type(turn_count)
    prompt = f"{_doubt_instructions(response_type)}\n\n{_doubt_input(concept, message, history, turn_count)}"
    response_text = _run_codex_json(prompt, "doubt_chat.schema.json")
    content = parse_doubt_response(response_text)
    return DoubtChatContent(response=content.response, response_type=response_type)


def grade_quiz_answer(
    concept: Concept,
    question: str,
    student_answer: str,
    rubric: str,
    taxonomy: list[dict[str, str]],
) -> QuizGradeContent:
    prompt = f"{_quiz_instructions()}\n\n{_quiz_input(concept, question, student_answer, rubric, taxonomy)}"
    response_text = _run_codex_json(prompt, "quiz_grade.schema.json")
    content = parse_quiz_grade_response(response_text)
    allowed_codes = {item["code"] for item in taxonomy}
    if content.misconception_code is not None and content.misconception_code not in allowed_codes:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Quiz grader returned a code outside the taxonomy")
    return content


def grade_teach_back(concept: Concept, correct_summary: str, student_explanation: str) -> TeachBackGradeContent:
    prompt = f"{_teach_back_instructions()}\n\n{_teach_back_input(concept, correct_summary, student_explanation)}"
    response_text = _run_codex_json(prompt, "teach_back.schema.json")
    return parse_teach_back_response(response_text)


def generate_confusion_narrative(
    concept_title: str,
    affected_student_count: int,
    total_students: int,
    misconceptions: list[dict[str, Any]],
) -> BriefNarrativeContent:
    prompt = (
        f"{_confusion_narrative_instructions()}\n\n"
        f"{_brief_narrative_input(concept_title, {'affected_student_count': affected_student_count, 'total_students': total_students, 'misconceptions': misconceptions})}"
    )
    response_text = _run_codex_json(prompt, "confusion_brief.schema.json")
    return parse_brief_narrative(response_text, "Confusion brief")


def generate_forecast_narrative(
    concept_title: str,
    at_risk_count: int,
    total_students: int,
    contributors: list[dict[str, Any]],
) -> BriefNarrativeContent:
    prompt = (
        f"{_forecast_narrative_instructions()}\n\n"
        f"{_brief_narrative_input(concept_title, {'at_risk_count': at_risk_count, 'total_students': total_students, 'contributing_concepts': contributors})}"
    )
    response_text = _run_codex_json(prompt, "forecast_brief.schema.json")
    return parse_brief_narrative(response_text, "Forecast brief")


def refine_curriculum_draft(board: str, class_level: str, subject_name: str, chapters: list[dict[str, Any]]) -> CurriculumDraftContent:
    prompt = (
        "Clean this extracted curriculum outline for a school teacher. Keep only syllabus-style chapter and topic names. "
        "Do not invent new chapters. Merge obvious OCR duplicates, remove page numbers/noise, and keep the result concise.\n\n"
        + json.dumps({"board": board, "class_level": class_level, "subject_name": subject_name, "chapters": chapters}, ensure_ascii=True)
    )
    response_text = _run_codex_json(prompt, "curriculum_draft.schema.json")
    content = _json_content(response_text, "Curriculum draft")
    chapters_value = content.get("chapters")
    if not isinstance(chapters_value, list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Curriculum draft response did not match the contract")
    cleaned: list[dict[str, Any]] = []
    for chapter in chapters_value[:30]:
        if not isinstance(chapter, dict) or not isinstance(chapter.get("title"), str):
            continue
        topics = chapter.get("topics", [])
        cleaned.append({"title": chapter["title"].strip()[:180], "topics": [str(topic).strip()[:180] for topic in topics if str(topic).strip()][:40] if isinstance(topics, list) else []})
    return CurriculumDraftContent(chapters=cleaned)


def doubt_response_type(turn_count: int) -> str:
    if turn_count <= 1:
        return "guiding_question"
    if turn_count == 2:
        return "hint"
    if turn_count == 3:
        return "worked_step"
    return "explanation"


def parse_tutorial_response(response_payload: dict[str, Any] | str) -> TutorialContent:
    if isinstance(response_payload, str):
        output_text = response_payload
    else:
        output_text = response_payload.get("output_text")
        if not isinstance(output_text, str):
            output_text = _extract_output_text(response_payload)

    try:
        content = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Tutorial response was not valid JSON") from exc

    explanation = content.get("explanation")
    analogy = content.get("analogy")
    worked_example = content.get("worked_example")
    visual = content.get("visual", "")
    if not isinstance(explanation, str) or not isinstance(worked_example, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Tutorial response did not match the contract")
    if not isinstance(analogy, str) or not isinstance(visual, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Tutorial response did not match the contract")
    return TutorialContent(explanation=explanation, analogy=analogy, worked_example=worked_example, visual=visual)


def parse_doubt_response(response_payload: dict[str, Any] | str) -> DoubtChatContent:
    content = _json_content(response_payload, "Doubt chat")
    response = content.get("response")
    response_type = content.get("response_type")
    if not isinstance(response, str) or not isinstance(response_type, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Doubt chat response did not match the contract")
    if response_type not in {"guiding_question", "hint", "worked_step", "explanation"}:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Doubt chat response_type was invalid")
    return DoubtChatContent(response=response, response_type=response_type)


def parse_quiz_grade_response(response_payload: dict[str, Any] | str) -> QuizGradeContent:
    content = _json_content(response_payload, "Quiz grade")
    is_correct = content.get("is_correct")
    misconception_code = content.get("misconception_code")
    misconception_summary = content.get("misconception_summary")
    confidence = content.get("confidence")
    follow_up_question = content.get("follow_up_question")
    if not isinstance(is_correct, bool):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Quiz grade is_correct was invalid")
    if misconception_code is not None and not isinstance(misconception_code, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Quiz grade misconception_code was invalid")
    if not isinstance(misconception_summary, str) or not isinstance(follow_up_question, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Quiz grade response did not match the contract")
    if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Quiz grade confidence was invalid")
    return QuizGradeContent(
        is_correct=is_correct,
        misconception_code=misconception_code,
        misconception_summary=misconception_summary,
        confidence=float(confidence),
        follow_up_question=follow_up_question,
    )


def parse_teach_back_response(response_payload: dict[str, Any] | str) -> TeachBackGradeContent:
    content = _json_content(response_payload, "Teach-back grade")
    clarity_score = content.get("clarity_score")
    accuracy_score = content.get("accuracy_score")
    gap_identified = content.get("gap_identified")
    encouragement = content.get("encouragement")
    if not isinstance(clarity_score, int | float) or clarity_score < 0 or clarity_score > 1:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Teach-back clarity_score was invalid")
    if not isinstance(accuracy_score, int | float) or accuracy_score < 0 or accuracy_score > 1:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Teach-back accuracy_score was invalid")
    if not isinstance(gap_identified, str) or not isinstance(encouragement, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Teach-back response did not match the contract")
    return TeachBackGradeContent(
        clarity_score=float(clarity_score),
        accuracy_score=float(accuracy_score),
        gap_identified=gap_identified,
        encouragement=encouragement,
    )


def parse_brief_narrative(response_payload: dict[str, Any] | str, label: str) -> BriefNarrativeContent:
    content = _json_content(response_payload, label)
    summary = content.get("summary")
    suggested_activity = content.get("suggested_activity")
    if not isinstance(summary, str) or not summary.strip():
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{label} summary was invalid")
    if not isinstance(suggested_activity, str) or not suggested_activity.strip():
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{label} suggested_activity was invalid")
    return BriefNarrativeContent(summary=summary, suggested_activity=suggested_activity)


def _json_content(response_payload: dict[str, Any] | str, label: str) -> dict[str, Any]:
    if isinstance(response_payload, str):
        output_text = response_payload
    else:
        output_text = response_payload.get("output_text")
        if not isinstance(output_text, str):
            output_text = _extract_output_text(response_payload)
    try:
        content = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{label} response was not valid JSON") from exc
    if not isinstance(content, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{label} response was not a JSON object")
    return content


def _run_codex_json(prompt: str, schema_filename: str) -> str:
    schema_path = Path(__file__).resolve().parent / "codex_schemas" / schema_filename
    if not schema_path.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Codex output schema is missing")

    with tempfile.TemporaryDirectory(prefix="confusionlayer-codex-") as temp_dir:
        output_path = Path(temp_dir) / "last-message.json"
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "read-only",
            "--json",
            "--model",
            codex_model(),
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            prompt,
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                cwd=temp_dir,
                text=True,
                timeout=codex_timeout_seconds(),
                check=False,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Codex CLI is not installed") from exc
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Codex inference timed out") from exc

        if result.returncode != 0:
            detail = _compact_codex_error(result.stdout, result.stderr)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Codex inference failed: {detail}")

        if not output_path.exists():
            detail = _compact_codex_error(result.stdout, result.stderr)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Codex did not write a final response: {detail}")

        return output_path.read_text(encoding="utf-8")


def _compact_codex_error(stdout: str, stderr: str) -> str:
    combined = "\n".join(part for part in (stderr.strip(), stdout.strip()) if part)
    if not combined:
        return "no diagnostic output"
    lines = combined.splitlines()
    return "\n".join(lines[-12:])[:1500]


def _extract_output_text(response_payload: dict[str, Any]) -> str:
    fragments: list[str] = []
    for item in response_payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                fragments.append(content["text"])
    if not fragments:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Tutorial response did not include text output")
    return "".join(fragments)


def _tutorial_instructions() -> str:
    return (
        "You are the Tutorial Generator for ConfusionLayer, writing for a school student. Return only valid JSON "
        "with exactly these keys: explanation, analogy, worked_example, visual.\n"
        "- explanation (180-260 words): a clear, standard explanation in plain language. Define the idea, then build "
        "understanding step by step; prefer short sentences; introduce any term the first time you use it.\n"
        "- analogy (2-4 sentences): one relatable everyday example or analogy that makes the idea click — an example "
        "should teach more than a definition.\n"
        "- worked_example: one concrete, fully worked example with the steps shown, so the student can follow the "
        "method, not just the answer.\n"
        "- visual: a compact but useful visual block (<= 16 lines). Prefer chart-ready tables for numeric "
        "relationships, comparison tables for contrast concepts, and labelled diagrams for spatial/process concepts. "
        "For a chart-ready table, use one x-axis row and one or more numeric series rows on separate lines, such as "
        "'Angle: 0deg 30deg 60deg 90deg' then 'sin: 0 0.50 0.87 1.00' then 'cos: 1.00 0.87 0.50 0'. "
        "If a visual would not genuinely help, return an empty string.\n"
        "Do not compute mastery scores. Do not invent curriculum scope beyond the provided concept context."
    )


def _self_start_instructions() -> str:
    return (
        "You are the Tutorial Generator for ConfusionLayer, handling a student's self-started topic that is "
        "OUTSIDE the official school syllabus. Return only valid JSON with exactly these keys: explanation, analogy, "
        "worked_example, visual.\n"
        "- explanation (180-260 words): clear, plain-language, standard explanation pitched at the reading level.\n"
        "- analogy: one relatable everyday example that makes the idea click.\n"
        "- worked_example: one concrete example with the steps shown.\n"
        "- visual: a compact but useful visual block (<= 16 lines). Prefer chart-ready tables for numeric "
        "relationships, comparison tables for contrast concepts, and labelled diagrams for spatial/process concepts. "
        "For chart-ready tables, use one x-axis row and one or more numeric series rows. Return an empty string only "
        "when a visual would not help.\n"
        "Stay on the student's topic; if the topic is unclear or not a real learning topic, give a brief, safe "
        "general explanation instead. Do not compute mastery scores."
    )


def _self_start_input(topic: str, reading_level: str, subject_context: dict[str, str]) -> str:
    return (
        f"Reading level: {reading_level}\n"
        f"Student's typical context (for pitching level only): "
        f"{subject_context.get('board', '')} {subject_context.get('class_level', '')} {subject_context.get('subject', '')}\n"
        f"Self-started topic (outside official syllabus): {topic}\n\n"
        "Generate a tutorial for this topic. Return JSON only: "
        "{\"explanation\": string, \"analogy\": string, \"worked_example\": string, \"visual\": string}."
    )


def _doubt_instructions(response_type: str) -> str:
    return (
        "You are the Socratic Tutor for ConfusionLayer. Return only valid JSON with exactly these keys: "
        "response and response_type. The response_type must be "
        f"{response_type}. Keep the answer aligned to the provided concept. For guiding_question and hint, do not "
        "give the final answer directly. For worked_step, show one step only. For explanation, give a concise answer "
        "and end with one follow-up check question."
    )


def _quiz_instructions() -> str:
    return (
        "You are the Grader/Diagnostician for ConfusionLayer. Return only valid JSON with exactly these keys: "
        "is_correct, misconception_code, misconception_summary, confidence, and follow_up_question. "
        "The misconception_code must be null or one of the provided taxonomy codes. Do not invent new codes. "
        "Do not compute mastery scores."
    )


def _teach_back_instructions() -> str:
    return (
        "You are the Teach-Back Grader for ConfusionLayer. Return only valid JSON with exactly these keys: "
        "clarity_score, accuracy_score, gap_identified, and encouragement. Scores must be numbers from 0 to 1. "
        "Grade whether the student can explain the concept in their own words. Do not compute mastery scores."
    )


def _tutorial_input(concept: Concept, reading_level: str) -> str:
    chapter = concept.chapter
    subject = chapter.subject
    return (
        f"Board: {subject.board}\n"
        f"Class level: {subject.class_level}\n"
        f"Subject: {subject.name}\n"
        f"Chapter: {chapter.title}\n"
        f"Concept: {concept.title}\n"
        f"Reading level: {reading_level}\n\n"
        "Generate a tutorial aligned to this concept with a clear explanation, an everyday analogy, one worked "
        "example, and a compact visual. If the concept has values, trends, or formulas, make visual a chart-ready "
        "table with an x-axis row and numeric series rows. Return JSON only: "
        "{\"explanation\": string, \"analogy\": string, \"worked_example\": string, \"visual\": string}."
    )


def _doubt_input(concept: Concept, message: str, history: list[dict[str, str]], turn_count: int) -> str:
    chapter = concept.chapter
    subject = chapter.subject
    compact_history = history[-6:]
    return (
        f"Board: {subject.board}\n"
        f"Class level: {subject.class_level}\n"
        f"Subject: {subject.name}\n"
        f"Chapter: {chapter.title}\n"
        f"Concept: {concept.title}\n"
        f"Turn count: {turn_count}\n"
        f"Recent chat history JSON: {json.dumps(compact_history, ensure_ascii=True)}\n"
        f"Student message: {message}\n"
    )


def _quiz_input(
    concept: Concept,
    question: str,
    student_answer: str,
    rubric: str,
    taxonomy: list[dict[str, str]],
) -> str:
    chapter = concept.chapter
    subject = chapter.subject
    return (
        f"Board: {subject.board}\n"
        f"Class level: {subject.class_level}\n"
        f"Subject: {subject.name}\n"
        f"Chapter: {chapter.title}\n"
        f"Concept: {concept.title}\n"
        f"Question: {question}\n"
        f"Student answer: {student_answer}\n"
        f"Rubric/correct answer: {rubric}\n"
        f"Allowed taxonomy JSON: {json.dumps(taxonomy, ensure_ascii=True)}\n"
    )


def _teach_back_input(concept: Concept, correct_summary: str, student_explanation: str) -> str:
    chapter = concept.chapter
    subject = chapter.subject
    return (
        f"Board: {subject.board}\n"
        f"Class level: {subject.class_level}\n"
        f"Subject: {subject.name}\n"
        f"Chapter: {chapter.title}\n"
        f"Concept: {concept.title}\n"
        f"Correct concept summary/rubric: {correct_summary}\n"
        f"Student explanation: {student_explanation}\n"
    )


def _confusion_narrative_instructions() -> str:
    return (
        "You are the Confusion Brief narrator for ConfusionLayer, writing for a teacher. Return only valid JSON "
        "with exactly these keys: summary and suggested_activity. The summary is 1-2 sentences describing where the "
        "class is confused, using ONLY the counts provided. The suggested_activity is one short, concrete classroom "
        "action (include an approximate time in minutes). Do not invent, recompute, or change any numbers. Do not "
        "name individual students. Do not compute mastery scores."
    )


def _forecast_narrative_instructions() -> str:
    return (
        "You are the Forecast Brief narrator for ConfusionLayer, writing a pre-lesson briefing for a teacher. Return "
        "only valid JSON with exactly these keys: summary and suggested_activity. The summary is 1-2 sentences stating "
        "how many students are predicted to struggle with the upcoming concept and which weak prerequisites are driving "
        "it, using ONLY the numbers provided. The suggested_activity is one short recap action to run before the lesson "
        "(include an approximate time in minutes). Do not invent, recompute, or change any numbers. Do not name "
        "individual students. Do not compute mastery or difficulty scores."
    )


def _brief_narrative_input(concept_title: str, payload: dict[str, Any]) -> str:
    return (
        f"Concept: {concept_title}\n"
        f"Deterministic figures (already computed, do not change) JSON: {json.dumps(payload, ensure_ascii=True)}\n"
    )
