import os
from datetime import date, datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import select
from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.ai import (
    check_and_increment_ai_usage,
    codex_model,
    generate_confusion_narrative,
    generate_doubt_response,
    generate_forecast_narrative,
    generate_self_start_tutorial,
    generate_tutorial,
    grade_quiz_answer,
    grade_teach_back,
)
from app.mastery import days_since_review, effective_mastery
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
from app.briefs import aggregate_confusion, aggregate_forecast
from app.db import get_db
from app.forecast import recompute_classroom_forecasts
from app.models import (
    Chapter,
    ChapterUnlock,
    Classroom,
    ClassroomStudent,
    Concept,
    ConfusionBrief,
    MasteryHistory,
    MasteryRecord,
    MisconceptionTaxonomy,
    QuizAttempt,
    Student,
    Subject,
    TeachBackAttempt,
    User,
)

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


class ChatMessage(BaseModel):
    role: str
    content: str


class DoubtChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)
    turn_count: int = 1


class DoubtChatResponse(BaseModel):
    response: str
    response_type: str


class QuizGradeRequest(BaseModel):
    question: str
    student_answer: str
    rubric: str


class QuizGradeResponse(BaseModel):
    is_correct: bool
    misconception_code: str | None
    misconception_summary: str
    confidence: float
    follow_up_question: str
    attempt_id: int


class TeachBackGradeRequest(BaseModel):
    student_explanation: str
    correct_summary: str


class TeachBackGradeResponse(BaseModel):
    clarity_score: float
    accuracy_score: float
    gap_identified: str
    encouragement: str
    attempt_id: int


class ForecastContributionResponse(BaseModel):
    concept_id: int
    title: str
    effective_mastery: float
    contribution_weight: float
    difficulty_component: float
    distance: int


class ForecastRecordResponse(BaseModel):
    id: int
    student_id: int
    concept_id: int
    predicted_difficulty: float
    contributing_concepts: list[ForecastContributionResponse]
    computed_at: datetime


class ForecastRecomputeResponse(BaseModel):
    classroom_id: int
    forecast_count: int
    forecasts: list[ForecastRecordResponse]


class MisconceptionClusterResponse(BaseModel):
    code: str
    description: str
    student_count: int


class ConfusionConceptResponse(BaseModel):
    concept_id: int
    concept_title: str
    chapter_title: str
    affected_student_count: int
    misconceptions: list[MisconceptionClusterResponse]


class ConfusionBriefResponse(BaseModel):
    classroom_id: int
    total_students: int
    privacy_threshold: int
    concepts: list[ConfusionConceptResponse]


class ForecastContributorResponse(BaseModel):
    concept_id: int
    title: str
    average_effective_mastery: float
    mention_count: int


class ForecastConceptResponse(BaseModel):
    concept_id: int
    concept_title: str
    chapter_title: str
    at_risk_count: int
    total_students: int
    average_difficulty: float
    top_contributors: list[ForecastContributorResponse]


class ForecastBriefResponse(BaseModel):
    classroom_id: int
    total_students: int
    at_risk_threshold: float
    computed_at: datetime | None
    concepts: list[ForecastConceptResponse]


class BriefNarrativeRequest(BaseModel):
    concept_id: int


class BriefNarrativeResponse(BaseModel):
    concept_id: int
    concept_title: str
    summary: str
    suggested_activity: str


class SelfStartRequest(BaseModel):
    topic: str
    reading_level: str = "Class 10"


class ProgressPointResponse(BaseModel):
    recorded_at: date
    mastery: float


class ProgressConceptResponse(BaseModel):
    concept_id: int
    concept_title: str
    chapter_title: str
    current_mastery: float
    effective_mastery: float
    history: list[ProgressPointResponse]


class ProgressSummaryResponse(BaseModel):
    concept_count: int
    mastered_count: int
    average_effective_mastery: float


class StudentProgressResponse(BaseModel):
    student_name: str
    mastered_threshold: float
    summary: ProgressSummaryResponse
    concepts: list[ProgressConceptResponse]


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
    classroom = _require_teacher_classroom(db, current_user, classroom_id, "unlock chapters")

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


@app.post("/api/teacher/classrooms/{classroom_id}/forecasts/recompute", response_model=ForecastRecomputeResponse)
def recompute_forecasts(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForecastRecomputeResponse:
    _require_teacher_classroom(db, current_user, classroom_id, "recompute forecasts")

    records = recompute_classroom_forecasts(db, classroom_id)
    return ForecastRecomputeResponse(
        classroom_id=classroom_id,
        forecast_count=len(records),
        forecasts=[
            ForecastRecordResponse(
                id=record.id,
                student_id=record.student_id,
                concept_id=record.concept_id,
                predicted_difficulty=record.predicted_difficulty,
                contributing_concepts=[
                    ForecastContributionResponse(
                        concept_id=int(item["concept_id"]),
                        title=str(item["title"]),
                        effective_mastery=float(item["effective_mastery"]),
                        contribution_weight=float(item["contribution_weight"]),
                        difficulty_component=float(item["difficulty_component"]),
                        distance=int(item["distance"]),
                    )
                    for item in record.contributing_concepts
                ],
                computed_at=record.computed_at,
            )
            for record in records
        ],
    )


@app.get("/api/teacher/classrooms/{classroom_id}/confusion-brief", response_model=ConfusionBriefResponse)
def confusion_brief(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConfusionBriefResponse:
    _require_teacher_classroom(db, current_user, classroom_id, "view the confusion brief")
    aggregate = aggregate_confusion(db, classroom_id)
    return ConfusionBriefResponse(
        classroom_id=aggregate.classroom_id,
        total_students=aggregate.total_students,
        privacy_threshold=aggregate.privacy_threshold,
        concepts=[
            ConfusionConceptResponse(
                concept_id=concept.concept_id,
                concept_title=concept.concept_title,
                chapter_title=concept.chapter_title,
                affected_student_count=concept.affected_student_count,
                misconceptions=[
                    MisconceptionClusterResponse(code=item.code, description=item.description, student_count=item.student_count)
                    for item in concept.misconceptions
                ],
            )
            for concept in aggregate.concepts
        ],
    )


@app.post("/api/teacher/classrooms/{classroom_id}/confusion-brief/narrative", response_model=BriefNarrativeResponse)
def confusion_brief_narrative(
    classroom_id: int,
    payload: BriefNarrativeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BriefNarrativeResponse:
    _require_teacher_classroom(db, current_user, classroom_id, "generate the confusion brief")
    aggregate = aggregate_confusion(db, classroom_id)
    concept = next((item for item in aggregate.concepts if item.concept_id == payload.concept_id), None)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No confusion data meets the privacy threshold for this concept",
        )

    check_and_increment_ai_usage(db, current_user)
    misconceptions = [
        {"code": item.code, "description": item.description, "student_count": item.student_count}
        for item in concept.misconceptions
    ]
    narrative = generate_confusion_narrative(
        concept.concept_title, concept.affected_student_count, aggregate.total_students, misconceptions
    )

    db.add(
        ConfusionBrief(
            classroom_id=classroom_id,
            concept_id=concept.concept_id,
            generated_text=f"{narrative.summary}\n\nSuggested activity: {narrative.suggested_activity}",
            affected_student_count=concept.affected_student_count,
            misconception_breakdown={item.code: item.student_count for item in concept.misconceptions},
        )
    )
    db.commit()

    return BriefNarrativeResponse(
        concept_id=concept.concept_id,
        concept_title=concept.concept_title,
        summary=narrative.summary,
        suggested_activity=narrative.suggested_activity,
    )


@app.get("/api/teacher/classrooms/{classroom_id}/forecast-brief", response_model=ForecastBriefResponse)
def forecast_brief(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForecastBriefResponse:
    _require_teacher_classroom(db, current_user, classroom_id, "view the forecast brief")
    aggregate = aggregate_forecast(db, classroom_id)
    return ForecastBriefResponse(
        classroom_id=aggregate.classroom_id,
        total_students=aggregate.total_students,
        at_risk_threshold=aggregate.at_risk_threshold,
        computed_at=aggregate.computed_at,
        concepts=[
            ForecastConceptResponse(
                concept_id=concept.concept_id,
                concept_title=concept.concept_title,
                chapter_title=concept.chapter_title,
                at_risk_count=concept.at_risk_count,
                total_students=concept.total_students,
                average_difficulty=concept.average_difficulty,
                top_contributors=[
                    ForecastContributorResponse(
                        concept_id=item.concept_id,
                        title=item.title,
                        average_effective_mastery=item.average_effective_mastery,
                        mention_count=item.mention_count,
                    )
                    for item in concept.top_contributors
                ],
            )
            for concept in aggregate.concepts
        ],
    )


@app.post("/api/teacher/classrooms/{classroom_id}/forecast-brief/narrative", response_model=BriefNarrativeResponse)
def forecast_brief_narrative(
    classroom_id: int,
    payload: BriefNarrativeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BriefNarrativeResponse:
    _require_teacher_classroom(db, current_user, classroom_id, "generate the forecast brief")
    aggregate = aggregate_forecast(db, classroom_id)
    concept = next((item for item in aggregate.concepts if item.concept_id == payload.concept_id), None)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No forecast data is available for this concept",
        )

    check_and_increment_ai_usage(db, current_user)
    contributors = [
        {
            "concept_id": item.concept_id,
            "title": item.title,
            "average_effective_mastery": item.average_effective_mastery,
            "mention_count": item.mention_count,
        }
        for item in concept.top_contributors
    ]
    narrative = generate_forecast_narrative(
        concept.concept_title, concept.at_risk_count, concept.total_students, contributors
    )

    return BriefNarrativeResponse(
        concept_id=concept.concept_id,
        concept_title=concept.concept_title,
        summary=narrative.summary,
        suggested_activity=narrative.suggested_activity,
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


@app.post("/api/concepts/{concept_id}/doubt-chat", response_model=DoubtChatResponse)
def doubt_chat(
    concept_id: int,
    payload: DoubtChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DoubtChatResponse:
    if current_user.role != "student" or current_user.student_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can use doubt chat")

    concept = _get_accessible_concept(db, current_user, concept_id)
    check_and_increment_ai_usage(db, current_user)
    history = [{"role": item.role, "content": item.content} for item in payload.history]
    content = generate_doubt_response(concept, payload.message, history, payload.turn_count)
    return DoubtChatResponse(response=content.response, response_type=content.response_type)


@app.post("/api/concepts/{concept_id}/quiz/grade", response_model=QuizGradeResponse)
def grade_quiz(
    concept_id: int,
    payload: QuizGradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizGradeResponse:
    if current_user.role != "student" or current_user.student_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can submit quiz attempts")

    concept = _get_accessible_concept(db, current_user, concept_id)
    taxonomy_rows = _taxonomy_for_concept(db, concept.id)
    taxonomy = [{"code": item.code, "description": item.description} for item in taxonomy_rows]
    check_and_increment_ai_usage(db, current_user)
    grade = grade_quiz_answer(concept, payload.question, payload.student_answer, payload.rubric, taxonomy)

    attempt = QuizAttempt(
        student_id=current_user.student_id,
        concept_id=concept.id,
        question=payload.question,
        student_answer=payload.student_answer,
        is_correct=grade.is_correct,
        misconception_code=grade.misconception_code,
        confidence=grade.confidence,
        mode="quiz",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return QuizGradeResponse(
        is_correct=grade.is_correct,
        misconception_code=grade.misconception_code,
        misconception_summary=grade.misconception_summary,
        confidence=grade.confidence,
        follow_up_question=grade.follow_up_question,
        attempt_id=attempt.id,
    )


@app.post("/api/concepts/{concept_id}/teach-back/grade", response_model=TeachBackGradeResponse)
def grade_teach_back_endpoint(
    concept_id: int,
    payload: TeachBackGradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeachBackGradeResponse:
    if current_user.role != "student" or current_user.student_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can submit teach-back attempts")

    concept = _get_accessible_concept(db, current_user, concept_id)
    check_and_increment_ai_usage(db, current_user)
    grade = grade_teach_back(concept, payload.correct_summary, payload.student_explanation)

    attempt = TeachBackAttempt(
        student_id=current_user.student_id,
        concept_id=concept.id,
        student_explanation=payload.student_explanation,
        clarity_score=grade.clarity_score,
        accuracy_score=grade.accuracy_score,
        gpt_feedback=f"Gap: {grade.gap_identified}\nEncouragement: {grade.encouragement}",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return TeachBackGradeResponse(
        clarity_score=grade.clarity_score,
        accuracy_score=grade.accuracy_score,
        gap_identified=grade.gap_identified,
        encouragement=grade.encouragement,
        attempt_id=attempt.id,
    )


MASTERED_THRESHOLD = 0.8


@app.post("/api/self-start/tutorial", response_model=TutorialResponse)
def self_start_tutorial(
    payload: SelfStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TutorialResponse:
    if current_user.role != "student" or current_user.student_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can self-start topics")

    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A topic is required")

    classroom = _get_user_classroom(db, current_user)
    subject = classroom.subject
    check_and_increment_ai_usage(db, current_user)
    content = generate_self_start_tutorial(
        topic,
        payload.reading_level,
        {"board": subject.board, "class_level": subject.class_level, "subject": subject.name},
    )
    return TutorialResponse(explanation=content.explanation, worked_example=content.worked_example)


@app.get("/api/student/progress", response_model=StudentProgressResponse)
def student_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProgressResponse:
    if current_user.role != "student" or current_user.student_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view their progress")

    student = db.get(Student, current_user.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    rows = db.execute(
        select(MasteryRecord, Concept.title, Chapter.title, Chapter.order, Concept.order)
        .join(Concept, Concept.id == MasteryRecord.concept_id)
        .join(Chapter, Chapter.id == Concept.chapter_id)
        .where(MasteryRecord.student_id == student.id)
        .order_by(Chapter.order, Concept.order)
    ).all()

    history_by_concept: dict[int, list[MasteryHistory]] = {}
    for point in db.scalars(
        select(MasteryHistory)
        .where(MasteryHistory.student_id == student.id)
        .order_by(MasteryHistory.recorded_at)
    ).all():
        history_by_concept.setdefault(point.concept_id, []).append(point)

    concepts: list[ProgressConceptResponse] = []
    effective_values: list[float] = []
    for record, concept_title, chapter_title, _chapter_order, _concept_order in rows:
        effective = effective_mastery(record.computed_mastery, days_since_review(record.last_reviewed_at))
        effective_values.append(effective)
        concepts.append(
            ProgressConceptResponse(
                concept_id=record.concept_id,
                concept_title=concept_title,
                chapter_title=chapter_title,
                current_mastery=record.computed_mastery,
                effective_mastery=effective,
                history=[
                    ProgressPointResponse(recorded_at=point.recorded_at, mastery=point.mastery)
                    for point in history_by_concept.get(record.concept_id, [])
                ],
            )
        )

    mastered = sum(1 for value in effective_values if value >= MASTERED_THRESHOLD)
    average = round(sum(effective_values) / len(effective_values), 4) if effective_values else 0.0
    return StudentProgressResponse(
        student_name=student.name,
        mastered_threshold=MASTERED_THRESHOLD,
        summary=ProgressSummaryResponse(
            concept_count=len(concepts),
            mastered_count=mastered,
            average_effective_mastery=average,
        ),
        concepts=concepts,
    )


def _require_teacher_classroom(db: Session, user: User, classroom_id: int, action: str) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    if user.role == "student" or (user.role == "teacher" and classroom.teacher_id != user.teacher_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Not allowed to {action} for this classroom")
    return classroom


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


def _taxonomy_for_concept(db: Session, concept_id: int) -> list[MisconceptionTaxonomy]:
    return list(
        db.scalars(
            select(MisconceptionTaxonomy).where(MisconceptionTaxonomy.concept_id == concept_id).order_by(MisconceptionTaxonomy.code)
        ).all()
    )


def _classroom_response(classroom: Classroom) -> ClassroomResponse:
    return ClassroomResponse(id=classroom.id, name=classroom.name, subject=_subject_response(classroom.subject))


def _subject_response(subject: Subject) -> SubjectResponse:
    return SubjectResponse(id=subject.id, name=subject.name, board=subject.board, class_level=subject.class_level)
