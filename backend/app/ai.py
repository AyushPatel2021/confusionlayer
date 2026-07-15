from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime
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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OPENAI_API_KEY is not configured")

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
        "instructions": _tutorial_instructions(),
        "input": _tutorial_input(concept, reading_level),
        "text": {"format": {"type": "json_object"}},
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"OpenAI API error: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OpenAI API request failed") from exc

    return parse_tutorial_response(response_payload)


def parse_tutorial_response(response_payload: dict[str, Any]) -> TutorialContent:
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
