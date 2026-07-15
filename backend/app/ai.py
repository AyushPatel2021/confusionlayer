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
    worked_example: str


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
    worked_example = content.get("worked_example")
    if not isinstance(explanation, str) or not isinstance(worked_example, str):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Tutorial response did not match the contract")
    return TutorialContent(explanation=explanation, worked_example=worked_example)


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
        "You are the Tutorial Generator for ConfusionLayer. Return only valid JSON with exactly "
        "these keys: explanation and worked_example. The explanation must be 200-300 words. "
        "Do not compute mastery scores. Do not invent curriculum scope beyond the provided concept context."
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
        "Generate a concise tutorial aligned to this concept. Include one simple worked example. "
        "Return JSON only: {\"explanation\": string, \"worked_example\": string}."
    )
