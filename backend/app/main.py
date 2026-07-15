import os
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import select
from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.ai import check_and_increment_ai_usage, codex_model, generate_tutorial
from app.auth import (
    AuthResponse,
    DemoLoginRequest,
    LoginRequest,
    SignupRequest,
    authenticate_user,
    clear_auth_cookie,
    create_access_token,
    create_user,
    get_current_user,
    get_or_create_demo_user,
    set_auth_cookie,
    user_response,
)
from app.db import get_db
from app.models import Chapter, ChapterUnlock, Classroom, ClassroomStudent, Concept, MisconceptionTaxonomy, Subject, User

app = FastAPI(title="ConfusionLayer API")


class SubjectResponse(BaseModel):
    id: int
    name: str
    board: str
    class_level: str


class ClassroomResponse(BaseModel):
    id: int
    name: str
    subject: SubjectResponse


class DemoContextResponse(BaseModel):
    classroom: ClassroomResponse
    teacher_count: int
    student_count: int


class ConceptSummaryResponse(BaseModel):
    id: int
    title: str
    order: int
    locked: bool


class ChapterSyllabusResponse(BaseModel):
    id: int
    title: str
    order: int
    locked: bool
    concepts: list[ConceptSummaryResponse]


class StudentSyllabusResponse(BaseModel):
    classroom: ClassroomResponse
    chapters: list[ChapterSyllabusResponse]


class ChapterUnlockResponse(BaseModel):
    id: int
    classroom_id: int
    chapter_id: int
    unlocked_by: int | None
    unlocked_at: datetime


class TaxonomyResponse(BaseModel):
    code: str
    description: str


class ConceptDetailResponse(BaseModel):
    id: int
    title: str
    order: int
    chapter_id: int
    chapter_title: str
    subject: SubjectResponse
    taxonomy: list[TaxonomyResponse]


class TutorialRequest(BaseModel):
    reading_level: str = "Class 10"


class TutorialResponse(BaseModel):
    explanation: str
    worked_example: str


@app.get("/api/health")
def health() -> dict[str, str | bool | int]:
    return {
        "ok": True,
        "service": "confusionlayer-backend",
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "ai_daily_call_limit": int(os.getenv("AI_DAILY_CALL_LIMIT", "50")),
        "codex_model": codex_model(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = create_user(db, payload)
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return AuthResponse(access_token=token, user=user_response(user))


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return AuthResponse(access_token=token, user=user_response(user))


@app.post("/api/auth/demo", response_model=AuthResponse)
def demo_login(payload: DemoLoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_or_create_demo_user(db, payload.role)
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return AuthResponse(access_token=token, user=user_response(user))


@app.get("/api/auth/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthResponse:
    token = create_access_token(current_user)
    return AuthResponse(access_token=token, user=user_response(current_user))


@app.post("/api/auth/logout")
def logout(response: Response) -> dict[str, bool]:
    clear_auth_cookie(response)
    return {"ok": True}


@app.get("/api/demo/context", response_model=DemoContextResponse)
def demo_context(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DemoContextResponse:
    classroom = _get_user_classroom(db, current_user)
    return DemoContextResponse(
        classroom=_classroom_response(classroom),
        teacher_count=1,
        student_count=len(classroom.students),
    )


@app.get("/api/student/syllabus", response_model=StudentSyllabusResponse)
def student_syllabus(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> StudentSyllabusResponse:
    classroom = _get_user_classroom(db, current_user)
    chapters = db.scalars(select(Chapter).where(Chapter.subject_id == classroom.subject_id).order_by(Chapter.order)).all()
    unlocked_ids = set(
        db.scalars(select(ChapterUnlock.chapter_id).where(ChapterUnlock.classroom_id == classroom.id)).all()
    )

    return StudentSyllabusResponse(
        classroom=_classroom_response(classroom),
        chapters=[
            ChapterSyllabusResponse(
                id=chapter.id,
                title=chapter.title,
                order=chapter.order,
                locked=chapter.id not in unlocked_ids,
                concepts=[
                    ConceptSummaryResponse(id=concept.id, title=concept.title, order=concept.order, locked=chapter.id not in unlocked_ids)
                    for concept in sorted(chapter.concepts, key=lambda item: item.order)
                ],
            )
            for chapter in chapters
        ],
    )


@app.post(
    "/api/teacher/classrooms/{classroom_id}/chapters/{chapter_id}/unlock",
    response_model=ChapterUnlockResponse,
)
def unlock_chapter(
    classroom_id: int,
    chapter_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChapterUnlockResponse:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    if current_user.role == "student" or (current_user.role == "teacher" and classroom.teacher_id != current_user.teacher_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to unlock this classroom")

    chapter = db.get(Chapter, chapter_id)
    if not chapter or chapter.subject_id != classroom.subject_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found for this classroom")

    unlock = db.scalar(
        select(ChapterUnlock).where(ChapterUnlock.classroom_id == classroom_id, ChapterUnlock.chapter_id == chapter_id)
    )
    if not unlock:
        unlock = ChapterUnlock(
            classroom_id=classroom_id,
            chapter_id=chapter_id,
            unlocked_by=current_user.teacher_id if current_user.role == "teacher" else None,
        )
        db.add(unlock)
        db.commit()
        db.refresh(unlock)

    return ChapterUnlockResponse(
        id=unlock.id,
        classroom_id=unlock.classroom_id,
        chapter_id=unlock.chapter_id,
        unlocked_by=unlock.unlocked_by,
        unlocked_at=unlock.unlocked_at,
    )


@app.get("/api/concepts/{concept_id}", response_model=ConceptDetailResponse)
def concept_detail(
    concept_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConceptDetailResponse:
    concept = _get_accessible_concept(db, current_user, concept_id)

    taxonomy = db.scalars(
        select(MisconceptionTaxonomy).where(MisconceptionTaxonomy.concept_id == concept.id).order_by(MisconceptionTaxonomy.code)
    ).all()
    return ConceptDetailResponse(
        id=concept.id,
        title=concept.title,
        order=concept.order,
        chapter_id=concept.chapter_id,
        chapter_title=concept.chapter.title,
        subject=_subject_response(concept.chapter.subject),
        taxonomy=[TaxonomyResponse(code=item.code, description=item.description) for item in taxonomy],
    )


@app.post("/api/concepts/{concept_id}/tutorial", response_model=TutorialResponse)
def tutorial(
    concept_id: int,
    payload: TutorialRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TutorialResponse:
    concept = _get_accessible_concept(db, current_user, concept_id)
    check_and_increment_ai_usage(db, current_user)
    content = generate_tutorial(concept, payload.reading_level)
    return TutorialResponse(explanation=content.explanation, worked_example=content.worked_example)


def _get_accessible_concept(db: Session, user: User, concept_id: int) -> Concept:
    concept = db.get(Concept, concept_id)
    if not concept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")

    classroom = _get_user_classroom(db, user)
    if concept.chapter.subject_id != classroom.subject_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found for this classroom")
    if user.role == "student" and not _is_chapter_unlocked(db, classroom.id, concept.chapter_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chapter is locked")
    return concept


def _get_user_classroom(db: Session, user: User) -> Classroom:
    if user.role == "teacher" and user.teacher_id:
        classroom = db.scalar(select(Classroom).where(Classroom.teacher_id == user.teacher_id).order_by(Classroom.id))
    elif user.role == "student" and user.student_id:
        classroom = db.scalar(
            select(Classroom)
            .join(ClassroomStudent, ClassroomStudent.classroom_id == Classroom.id)
            .where(ClassroomStudent.student_id == user.student_id)
            .order_by(Classroom.id)
        )
    elif user.role == "admin":
        classroom = db.scalar(select(Classroom).order_by(Classroom.id))
    else:
        classroom = None

    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No classroom is available for this user")
    return classroom


def _is_chapter_unlocked(db: Session, classroom_id: int, chapter_id: int) -> bool:
    return bool(
        db.scalar(select(ChapterUnlock.id).where(ChapterUnlock.classroom_id == classroom_id, ChapterUnlock.chapter_id == chapter_id))
    )


def _classroom_response(classroom: Classroom) -> ClassroomResponse:
    return ClassroomResponse(id=classroom.id, name=classroom.name, subject=_subject_response(classroom.subject))


def _subject_response(subject: Subject) -> SubjectResponse:
    return SubjectResponse(id=subject.id, name=subject.name, board=subject.board, class_level=subject.class_level)
