"""Curriculum authoring + structural PDF import.

Import extracts ONLY the structural skeleton (chapter / topic headings) from an
uploaded document, in memory — the raw PDF is never written to disk or the DB.
Extraction is heuristic (PDF outline/bookmarks first, then a heading heuristic
over the text); a human always reviews and edits the draft tree before it is
saved as real curriculum rows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models import Chapter, Concept, Subject

_CHAPTER_RE = re.compile(r"^\s*(chapter|unit|module)\b", re.IGNORECASE)
_NUMBERED_RE = re.compile(r"^\s*\d+(\.\d+)*[.)]?\s+\S")


@dataclass
class DraftChapter:
    title: str
    topics: list[str]


def _looks_like_chapter(line: str) -> bool:
    return bool(_CHAPTER_RE.match(line)) or bool(re.match(r"^\s*\d+[.)]\s+\S", line))


def structure_from_headings(headings: list[str]) -> list[DraftChapter]:
    """Turn a flat, ordered list of heading strings into a chapter/topic tree.

    Chapter-like headings ("Chapter 3", "Unit 1", "2. Acids") open a chapter;
    other headings become topics under the most recent chapter. If nothing looks
    like a chapter, every heading becomes its own chapter.
    """
    cleaned = [h.strip() for h in headings if h and h.strip()]
    chapters: list[DraftChapter] = []
    for heading in cleaned:
        if _looks_like_chapter(heading) or not chapters:
            chapters.append(DraftChapter(title=heading, topics=[]))
        else:
            chapters[-1].topics.append(heading)

    # If NOTHING was chapter-like, the "most recent chapter" heuristic collapsed
    # everything under the first heading — treat each heading as its own chapter.
    if len(chapters) == 1 and not any(_looks_like_chapter(h) for h in cleaned) and chapters[0].topics:
        chapters = [DraftChapter(title=h, topics=[]) for h in cleaned]
    return chapters


def extract_headings(pdf_bytes: bytes) -> list[str]:
    """Extract candidate headings from a PDF (outline first, then heuristic)."""
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))

    outline_titles = _flatten_outline(getattr(reader, "outline", []) or [])
    if outline_titles:
        return outline_titles

    headings: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw in text.splitlines():
            line = raw.strip()
            if not line or len(line) > 80:
                continue
            if _looks_like_chapter(line) or _NUMBERED_RE.match(line) or (line.istitle() and len(line.split()) <= 8):
                if line not in headings:
                    headings.append(line)
    return headings


def _flatten_outline(outline: object) -> list[str]:
    titles: list[str] = []
    if isinstance(outline, list):
        for item in outline:
            titles.extend(_flatten_outline(item))
    else:
        title = getattr(outline, "title", None)
        if isinstance(title, str) and title.strip():
            titles.append(title.strip())
    return titles


def extract_structure(pdf_bytes: bytes) -> list[DraftChapter]:
    return structure_from_headings(extract_headings(pdf_bytes))


def commit_subject_tree(
    db: Session,
    org_id: int | None,
    name: str,
    board: str,
    class_level: str,
    chapters: list[DraftChapter],
) -> Subject:
    subject = Subject(org_id=org_id, name=name.strip(), board=board.strip(), class_level=class_level.strip())
    db.add(subject)
    db.flush()
    for chapter_index, draft in enumerate(chapters, start=1):
        chapter = Chapter(subject_id=subject.id, title=draft.title.strip()[:180], order=chapter_index)
        db.add(chapter)
        db.flush()
        for topic_index, topic in enumerate(draft.topics, start=1):
            db.add(Concept(chapter_id=chapter.id, title=topic.strip()[:180], order=topic_index))
    db.commit()
    db.refresh(subject)
    return subject
