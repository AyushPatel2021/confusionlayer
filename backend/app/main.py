import csv
import io
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile, status
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
    ForgotPasswordRequest,
    InvitationAcceptRequest,
    InvitationCreateRequest,
    InvitationPreviewResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SignupRequest,
    accept_invitation,
    authenticate_user,
    clear_auth_cookie,
    create_access_token,
    create_invitation,
    create_user,
    get_current_user,
    get_open_invitation,
    get_or_create_demo_user,
    register_org,
    request_password_reset,
    reset_password,
    set_auth_cookie,
    user_response,
)
from app.briefs import aggregate_confusion, aggregate_forecast
from app.curriculum import DraftChapter, commit_subject_tree, extract_structure
from app.db import get_db
from app.forecast import recompute_classroom_forecasts
from app.models import (
    AdmissionApplication,
    AttendanceRecord,
    AuditLog,
    Chapter,
    ChapterUnlock,
    Classroom,
    ClassroomStudent,
    Concept,
    ConfusionBrief,
    ForecastRecord,
    Employee,
    DEPARTMENTS,
    FeeStructure,
    GuardianLink,
    Invitation,
    Invoice,
    InvoiceLineItem,
    MasteryHistory,
    MasteryRecord,
    MisconceptionTaxonomy,
    Organization,
    Notification,
    Payment,
    PayrollRun,
    Payslip,
    Plan,
    QuizAttempt,
    Student,
    StudentTransportAssignment,
    Subject,
    Subscription,
    Teacher,
    TeachBackAttempt,
    TimetableEntry,
    TransportRoute,
    User,
    LibraryBook,
    LibraryLoan,
)

app = FastAPI(title="Slate API")


class SubjectResponse(BaseModel):
    id: int
    name: str
    board: str
    class_level: str


class ClassroomResponse(BaseModel):
    id: int
    name: str
    subject: SubjectResponse


class ClassroomMemberResponse(BaseModel):
    id: int
    name: str


class ManagedClassroomResponse(ClassroomResponse):
    teacher: ClassroomMemberResponse
    students: list[ClassroomMemberResponse]


class ClassroomCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    subject_id: int
    teacher_id: int


class ClassroomUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    subject_id: int
    teacher_id: int


class ClassroomEnrollmentRequest(BaseModel):
    student_id: int


class ClassroomOptionsResponse(BaseModel):
    subjects: list[SubjectResponse]
    teachers: list[ClassroomMemberResponse]
    students: list[ClassroomMemberResponse]


class DashboardMetricResponse(BaseModel):
    label: str
    value: str
    note: str | None = None


class DashboardChartResponse(BaseModel):
    label: str
    labels: list[str]
    values: list[float]


class DashboardResponse(BaseModel):
    role: str
    title: str
    metrics: list[DashboardMetricResponse]
    chart: DashboardChartResponse
    classrooms: list[ManagedClassroomResponse] = Field(default_factory=list)


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
    analogy: str = ""
    worked_example: str
    visual: str = ""


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
    mode: Literal["quiz", "exam"] = "quiz"


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


class StudentInsightConceptResponse(BaseModel):
    concept_id: int
    title: str
    chapter_title: str
    effective_mastery: float
    forecast_risk: float | None = None


class StudentInsightsResponse(BaseModel):
    student_id: int
    student_name: str
    average_effective_mastery: float
    strengths: list[StudentInsightConceptResponse]
    weaknesses: list[StudentInsightConceptResponse]
    concepts: list[StudentInsightConceptResponse]


class ExamOutcomeItemResponse(BaseModel):
    concept_id: int
    title: str
    chapter_title: str
    risk: float
    effective_mastery: float


class ExamOutcomeResponse(BaseModel):
    days_to_exam: int
    outcomes: list[ExamOutcomeItemResponse]


class SubjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    board: str = Field(default="CBSE", max_length=80)
    class_level: str = Field(default="10", max_length=80)


class ChapterCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)


class ConceptCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)


class DraftChapterModel(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    topics: list[str] = Field(default_factory=list)


class ImportCommitRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    board: str = Field(default="CBSE", max_length=80)
    class_level: str = Field(default="10", max_length=80)
    chapters: list[DraftChapterModel] = Field(default_factory=list)


class CurriculumSubjectResponse(BaseModel):
    id: int
    name: str
    board: str
    class_level: str
    org_id: int | None
    shared: bool
    chapter_count: int


class CurriculumConceptNode(BaseModel):
    id: int
    title: str
    order: int


class CurriculumChapterNode(BaseModel):
    id: int
    title: str
    order: int
    concepts: list[CurriculumConceptNode]


class CurriculumTreeResponse(BaseModel):
    id: int
    name: str
    board: str
    class_level: str
    org_id: int | None
    chapters: list[CurriculumChapterNode]


class ImportDraftResponse(BaseModel):
    chapters: list[DraftChapterModel]


class PlanResponse(BaseModel):
    code: str
    name: str
    segment: str
    price_cents: int
    limits: dict[str, object]
    features: list[str]


class OrgUsageResponse(BaseModel):
    members: int
    students: int
    classrooms: int


class SubscriptionResponse(BaseModel):
    status: str
    plan: PlanResponse | None


class OrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    segment: str
    subscription: SubscriptionResponse | None
    usage: OrgUsageResponse


class MemberResponse(BaseModel):
    id: int
    name: str | None
    email: str
    role: str
    status: str
    department: str
    profile: dict[str, str] = Field(default_factory=dict)


class PendingInvitationResponse(BaseModel):
    id: int
    email: str
    role: str
    department: str


class MembersResponse(BaseModel):
    members: list[MemberResponse]
    pending: list[PendingInvitationResponse]


class ChangeRoleRequest(BaseModel):
    role: Literal["school_admin", "accountant", "hr", "teacher", "parent"]


class ChangeMemberStatusRequest(BaseModel):
    status: Literal["active", "inactive"]


class ChangeMemberDepartmentRequest(BaseModel):
    department: str = Field(min_length=2, max_length=80)


class ChangePlanRequest(BaseModel):
    plan_code: str


class ApplicationCreateRequest(BaseModel):
    applicant_name: str = Field(min_length=1, max_length=160)
    applicant_email: str | None = Field(default=None, max_length=255)
    grade: str | None = Field(default=None, max_length=80)
    source: str | None = Field(default=None, max_length=80)
    date_of_birth: date | None = None
    notes: str | None = None


class ApplicationStatusRequest(BaseModel):
    status: Literal["reviewing", "accepted", "rejected"]


class ApplicationResponse(BaseModel):
    id: int
    applicant_name: str
    applicant_email: str | None
    grade: str | None
    source: str | None
    date_of_birth: date | None
    notes: str | None
    status: str
    student_id: int | None
    created_at: datetime
    updated_at: datetime


# --- M8: fees ---
class FeeStructureCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    amount_cents: int = Field(ge=0)


class FeeStructureResponse(BaseModel):
    id: int
    name: str
    amount_cents: int


class InvoiceCreateRequest(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=160)
    amount_cents: int = Field(ge=0)
    description: str | None = Field(default=None, max_length=255)
    student_id: int | None = None
    due_date: date | None = None
    line_items: list["InvoiceLineItemRequest"] = Field(default_factory=list, max_length=25)


class InvoiceLineItemRequest(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    amount_cents: int = Field(ge=0)


class InvoiceLineItemResponse(InvoiceLineItemRequest):
    id: int


class PaymentCreateRequest(BaseModel):
    amount_cents: int = Field(gt=0)
    method: str | None = Field(default=None, max_length=60)
    note: str | None = Field(default=None, max_length=255)


class InvoiceResponse(BaseModel):
    id: int
    student_id: int | None
    recipient_name: str
    description: str | None
    amount_cents: int
    paid_cents: int
    status: str
    voided: bool
    due_date: date | None
    line_items: list[InvoiceLineItemResponse]
    created_at: datetime


class FeesSummaryResponse(BaseModel):
    billed_cents: int
    collected_cents: int
    outstanding_cents: int
    invoice_count: int


# --- M9: HR ---
class EmployeeCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=255)
    designation: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    join_date: date | None = None
    salary_cents: int = Field(default=0, ge=0)


class EmployeeStatusRequest(BaseModel):
    status: Literal["active", "inactive"]


class PayrollRunCreateRequest(BaseModel):
    period: str = Field(min_length=1, max_length=20)


class OrganizationSettingsRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    logo_url: str | None = Field(default=None, max_length=500)
    timezone: str = Field(default="Asia/Kolkata", max_length=80)
    currency: str = Field(default="INR", min_length=3, max_length=3)


class AttendanceEntryRequest(BaseModel):
    student_id: int
    status: Literal["present", "absent", "late", "excused"]
    note: str | None = Field(default=None, max_length=255)


class AttendanceRequest(BaseModel):
    attendance_date: date
    entries: list[AttendanceEntryRequest] = Field(min_length=1)


class TimetableEntryRequest(BaseModel):
    classroom_id: int
    weekday: int = Field(ge=0, le=6)
    starts_at: str = Field(min_length=5, max_length=5)
    ends_at: str = Field(min_length=5, max_length=5)
    room: str | None = Field(default=None, max_length=80)


class LibraryBookRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    author: str | None = Field(default=None, max_length=160)
    isbn: str | None = Field(default=None, max_length=32)
    copies_total: int = Field(default=1, ge=1)


class LibraryLoanRequest(BaseModel):
    student_id: int
    due_date: date | None = None


class TransportRouteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    vehicle_label: str | None = Field(default=None, max_length=120)
    driver_name: str | None = Field(default=None, max_length=160)
    stops: list[str] = Field(default_factory=list)


class TransportAssignmentRequest(BaseModel):
    student_id: int
    route_id: int
    stop_name: str | None = Field(default=None, max_length=160)


class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str | None
    designation: str | None
    phone: str | None
    join_date: date | None
    salary_cents: int
    status: str


class PayslipResponse(BaseModel):
    id: int
    employee_name: str
    gross_cents: int
    net_cents: int


class PayrollRunResponse(BaseModel):
    id: int
    period: str
    status: str
    payslip_count: int
    total_net_cents: int
    created_at: datetime


class PayrollRunDetailResponse(BaseModel):
    id: int
    period: str
    status: str
    payslips: list[PayslipResponse]


# --- M10: parent portal ---
class GuardianLinkRequest(BaseModel):
    parent_email: str = Field(min_length=3, max_length=255)
    student_id: int


class ChildSummaryResponse(BaseModel):
    student_id: int
    name: str
    admission_status: str | None
    outstanding_cents: int
    average_mastery: float | None


# --- M11: platform admin ---
class AdminOrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    segment: str
    plan_code: str | None
    member_count: int


class AdminUsageResponse(BaseModel):
    orgs: int
    users: int
    students: int
    invoices: int
    employees: int
    applications: int


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


def _auth_response(db: Session, user: User, response: Response) -> AuthResponse:
    token = create_access_token(user)
    set_auth_cookie(response, token)
    organization = db.get(Organization, user.org_id) if user.org_id else None
    return AuthResponse(user=user_response(user, organization))


@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user, organization = register_org(db, payload)
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return AuthResponse(user=user_response(user, organization))


@app.post("/api/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = create_user(db, payload)
    return _auth_response(db, user, response)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _auth_response(db, user, response)


@app.post("/api/auth/demo", response_model=AuthResponse)
def demo_login(payload: DemoLoginRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_or_create_demo_user(db, payload.role)
    return _auth_response(db, user, response)


@app.post("/api/auth/password/forgot")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    request_password_reset(db, payload.email)
    return {"ok": True}


@app.post("/api/auth/password/reset")
def do_reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, bool]:
    reset_password(db, payload.token, payload.password)
    return {"ok": True}


@app.get("/api/auth/invitations/{token}", response_model=InvitationPreviewResponse)
def invitation_preview(token: str, db: Session = Depends(get_db)) -> InvitationPreviewResponse:
    invitation = get_open_invitation(db, token)
    organization = db.get(Organization, invitation.org_id)
    return InvitationPreviewResponse(
        email=invitation.email,
        role=invitation.role,
        department=invitation.department,
        organization_name=organization.name if organization else "",
    )


@app.post("/api/auth/invitations/accept", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def invitation_accept(payload: InvitationAcceptRequest, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    user, organization = accept_invitation(db, payload.token, payload.password, payload.name, payload.profile)
    token = create_access_token(user)
    set_auth_cookie(response, token)
    return AuthResponse(user=user_response(user, organization))


@app.post("/api/org/invitations", status_code=status.HTTP_201_CREATED)
def create_org_invitation(
    payload: InvitationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    organization = _require_school_owner(current_user, db)
    if payload.department not in DEPARTMENTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a valid department")

    # Plan gating: don't let a student invite push the org past its plan's student cap.
    if payload.role == "student":
        subscription = _org_subscription(db, organization.id)
        plan = db.get(Plan, subscription.plan_id) if subscription else None
        max_students = (plan.limits or {}).get("max_students") if plan else None
        if isinstance(max_students, int):
            current_students = db.scalar(select(func.count(User.id)).where(User.org_id == organization.id, User.role == "student")) or 0
            if current_students >= max_students:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your plan allows {max_students} students. Upgrade to invite more.",
                )

    invitation = create_invitation(db, organization, current_user, payload.email, payload.role, payload.department)
    return {"token": invitation.token, "email": invitation.email, "role": invitation.role, "department": invitation.department}


@app.get("/api/auth/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AuthResponse:
    organization = db.get(Organization, current_user.org_id) if current_user.org_id else None
    return AuthResponse(user=user_response(current_user, organization))


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
    return TutorialResponse(explanation=content.explanation, analogy=content.analogy, worked_example=content.worked_example, visual=content.visual)


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
        mode=payload.mode,
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
    return TutorialResponse(explanation=content.explanation, analogy=content.analogy, worked_example=content.worked_example, visual=content.visual)


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


@app.get("/api/student/exam-outcome", response_model=ExamOutcomeResponse)
def student_exam_outcome(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ExamOutcomeResponse:
    if current_user.role != "student" or not current_user.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can view exam outcomes")
    progress = student_progress(current_user=current_user, db=db)
    mastery = {item.concept_id: item.effective_mastery for item in progress.concepts}
    rows = db.execute(select(ForecastRecord, Concept, Chapter).join(Concept, ForecastRecord.concept_id == Concept.id).join(Chapter, Concept.chapter_id == Chapter.id).where(ForecastRecord.student_id == current_user.student_id)).all()
    outcomes = sorted([ExamOutcomeItemResponse(concept_id=concept.id, title=concept.title, chapter_title=chapter.title, risk=forecast.predicted_difficulty, effective_mastery=mastery.get(concept.id, 0)) for forecast, concept, chapter in rows], key=lambda item: item.risk, reverse=True)[:5]
    today = date.today(); exam = date(today.year if today.month < 3 else today.year + 1, 3, 1)
    return ExamOutcomeResponse(days_to_exam=(exam - today).days, outcomes=outcomes)


@app.get("/api/teacher/classrooms/{classroom_id}/students/{student_id}/insights", response_model=StudentInsightsResponse)
def student_insights(
    classroom_id: int,
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentInsightsResponse:
    classroom = _require_teacher_classroom(db, current_user, classroom_id, "view student insights")
    if not db.scalar(select(ClassroomStudent.id).where(ClassroomStudent.classroom_id == classroom.id, ClassroomStudent.student_id == student_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this classroom")
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    records = db.execute(
        select(MasteryRecord, Concept, Chapter)
        .join(Concept, MasteryRecord.concept_id == Concept.id)
        .join(Chapter, Concept.chapter_id == Chapter.id)
        .where(MasteryRecord.student_id == student.id, Chapter.subject_id == classroom.subject_id)
    ).all()
    risks = {
        row.concept_id: row.predicted_difficulty
        for row in db.scalars(select(ForecastRecord).where(ForecastRecord.student_id == student.id)).all()
    }
    concepts = [
        StudentInsightConceptResponse(
            concept_id=concept.id,
            title=concept.title,
            chapter_title=chapter.title,
            effective_mastery=effective_mastery(record.computed_mastery, days_since_review(record.last_reviewed_at)),
            forecast_risk=risks.get(concept.id),
        )
        for record, concept, chapter in records
    ]
    ranked = sorted(concepts, key=lambda item: item.effective_mastery)
    return StudentInsightsResponse(
        student_id=student.id,
        student_name=student.name,
        average_effective_mastery=round(sum(item.effective_mastery for item in concepts) / len(concepts), 3) if concepts else 0,
        strengths=list(reversed(ranked[-3:])),
        weaknesses=ranked[:3],
        concepts=ranked,
    )


@dataclass
class CurrentContext:
    user: User
    organization: Organization | None
    role: str


def get_current_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentContext:
    organization = db.get(Organization, current_user.org_id) if current_user.org_id else None
    return CurrentContext(user=current_user, organization=organization, role=current_user.role)


def _cross_org(user: User, classroom: Classroom) -> bool:
    """True when both the user and the classroom are org-scoped and their orgs differ.

    Platform admins (no org) are exempt. Multi-tenant isolation guarantee for M1;
    tightened to non-null org_id in a later milestone.
    """
    if user.role == "platform_admin":
        return False
    return user.org_id is not None and classroom.org_id is not None and classroom.org_id != user.org_id


CURRICULUM_EDITOR_ROLES = {"owner", "school_admin", "teacher", "admin"}
MAX_IMPORT_BYTES = 5 * 1024 * 1024


def _require_curriculum_editor(user: User) -> None:
    if user.role not in CURRICULUM_EDITOR_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to manage curriculum")


def _editable_subject(db: Session, user: User, subject_id: int) -> Subject:
    _require_curriculum_editor(user)
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    if subject.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This curriculum is read-only for your organization")
    return subject


def _subject_tree_response(subject: Subject) -> CurriculumTreeResponse:
    return CurriculumTreeResponse(
        id=subject.id,
        name=subject.name,
        board=subject.board,
        class_level=subject.class_level,
        org_id=subject.org_id,
        chapters=[
            CurriculumChapterNode(
                id=chapter.id,
                title=chapter.title,
                order=chapter.order,
                concepts=[
                    CurriculumConceptNode(id=concept.id, title=concept.title, order=concept.order)
                    for concept in sorted(chapter.concepts, key=lambda c: c.order)
                ],
            )
            for chapter in sorted(subject.chapters, key=lambda c: c.order)
        ],
    )


@app.get("/api/curriculum/subjects", response_model=list[CurriculumSubjectResponse])
def list_curriculum_subjects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[CurriculumSubjectResponse]:
    _require_curriculum_editor(current_user)
    subjects = db.scalars(
        select(Subject).where(or_(Subject.org_id == current_user.org_id, Subject.org_id.is_(None))).order_by(Subject.id)
    ).all()
    return [
        CurriculumSubjectResponse(
            id=subject.id,
            name=subject.name,
            board=subject.board,
            class_level=subject.class_level,
            org_id=subject.org_id,
            shared=subject.org_id is None,
            chapter_count=len(subject.chapters),
        )
        for subject in subjects
    ]


@app.post("/api/curriculum/subjects", response_model=CurriculumSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_curriculum_subject(payload: SubjectCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumSubjectResponse:
    _require_curriculum_editor(current_user)
    subject = Subject(org_id=current_user.org_id, name=payload.name.strip(), board=payload.board.strip(), class_level=payload.class_level.strip())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return CurriculumSubjectResponse(
        id=subject.id, name=subject.name, board=subject.board, class_level=subject.class_level, org_id=subject.org_id, shared=False, chapter_count=0
    )


@app.patch("/api/curriculum/subjects/{subject_id}", response_model=CurriculumSubjectResponse)
def update_curriculum_subject(subject_id: int, payload: SubjectCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumSubjectResponse:
    subject = _editable_subject(db, current_user, subject_id)
    subject.name, subject.board, subject.class_level = payload.name.strip(), payload.board.strip(), payload.class_level.strip()
    db.commit()
    return CurriculumSubjectResponse(id=subject.id, name=subject.name, board=subject.board, class_level=subject.class_level, org_id=subject.org_id, shared=False, chapter_count=len(subject.chapters))


@app.delete("/api/curriculum/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum_subject(subject_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    db.delete(_editable_subject(db, current_user, subject_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/curriculum/subjects/{subject_id}", response_model=CurriculumTreeResponse)
def get_curriculum_subject(subject_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumTreeResponse:
    _require_curriculum_editor(current_user)
    subject = db.get(Subject, subject_id)
    if not subject or subject.org_id not in (None, current_user.org_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return _subject_tree_response(subject)


@app.post("/api/curriculum/subjects/{subject_id}/chapters", response_model=CurriculumChapterNode, status_code=status.HTTP_201_CREATED)
def add_curriculum_chapter(subject_id: int, payload: ChapterCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumChapterNode:
    subject = _editable_subject(db, current_user, subject_id)
    next_order = 1 + max((chapter.order for chapter in subject.chapters), default=0)
    chapter = Chapter(subject_id=subject.id, title=payload.title.strip(), order=next_order)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return CurriculumChapterNode(id=chapter.id, title=chapter.title, order=chapter.order, concepts=[])


@app.post("/api/curriculum/chapters/{chapter_id}/concepts", response_model=CurriculumConceptNode, status_code=status.HTTP_201_CREATED)
def add_curriculum_concept(chapter_id: int, payload: ConceptCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumConceptNode:
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    _editable_subject(db, current_user, chapter.subject_id)
    next_order = 1 + max((concept.order for concept in chapter.concepts), default=0)
    concept = Concept(chapter_id=chapter.id, title=payload.title.strip(), order=next_order)
    db.add(concept)
    db.commit()
    db.refresh(concept)
    return CurriculumConceptNode(id=concept.id, title=concept.title, order=concept.order)


@app.patch("/api/curriculum/chapters/{chapter_id}", response_model=CurriculumChapterNode)
def update_curriculum_chapter(chapter_id: int, payload: ChapterCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumChapterNode:
    chapter = db.get(Chapter, chapter_id)
    if not chapter: raise HTTPException(status_code=404, detail="Chapter not found")
    _editable_subject(db, current_user, chapter.subject_id)
    chapter.title = payload.title.strip(); db.commit()
    return CurriculumChapterNode(id=chapter.id, title=chapter.title, order=chapter.order, concepts=[CurriculumConceptNode(id=c.id, title=c.title, order=c.order) for c in chapter.concepts])


@app.delete("/api/curriculum/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum_chapter(chapter_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    chapter = db.get(Chapter, chapter_id)
    if not chapter: raise HTTPException(status_code=404, detail="Chapter not found")
    _editable_subject(db, current_user, chapter.subject_id); db.delete(chapter); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.patch("/api/curriculum/concepts/{concept_id}", response_model=CurriculumConceptNode)
def update_curriculum_concept(concept_id: int, payload: ConceptCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumConceptNode:
    concept = db.get(Concept, concept_id)
    if not concept: raise HTTPException(status_code=404, detail="Topic not found")
    _editable_subject(db, current_user, concept.chapter.subject_id)
    concept.title = payload.title.strip(); db.commit()
    return CurriculumConceptNode(id=concept.id, title=concept.title, order=concept.order)


@app.delete("/api/curriculum/concepts/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum_concept(concept_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    concept = db.get(Concept, concept_id)
    if not concept: raise HTTPException(status_code=404, detail="Topic not found")
    _editable_subject(db, current_user, concept.chapter.subject_id); db.delete(concept); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/curriculum/import", response_model=ImportDraftResponse)
def import_curriculum_pdf(file: UploadFile = File(...), current_user: User = Depends(get_current_user)) -> ImportDraftResponse:
    _require_curriculum_editor(current_user)
    contents = file.file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty")
    if len(contents) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 5MB)")
    try:
        drafts = extract_structure(contents)
    except Exception as exc:  # noqa: BLE001 - surface a clean error, never persist the raw file
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not read structure from that document") from exc
    # `contents` is only referenced here; it is never written to disk or the DB.
    return ImportDraftResponse(chapters=[DraftChapterModel(title=d.title, topics=d.topics) for d in drafts])


@app.post("/api/curriculum/import/commit", response_model=CurriculumTreeResponse, status_code=status.HTTP_201_CREATED)
def commit_curriculum_import(payload: ImportCommitRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> CurriculumTreeResponse:
    _require_curriculum_editor(current_user)
    if not payload.chapters:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one chapter is required")
    drafts = [DraftChapter(title=chapter.title, topics=list(chapter.topics)) for chapter in payload.chapters]
    subject = commit_subject_tree(db, current_user.org_id, payload.name, payload.board, payload.class_level, drafts)
    return _subject_tree_response(subject)


ORG_ADMIN_ROLES = {"owner", "school_admin", "admin"}
OWNER_ROLES = {"owner", "admin"}


def _require_org_admin(user: User) -> None:
    if user.role not in ORG_ADMIN_ROLES or not user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an owner or school admin can manage the organization")


def _require_school_owner(user: User, db: Session) -> Organization:
    if user.role != "owner" or not user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the school owner can manage members")
    org = _current_org(db, user)
    if org.segment != "school":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Member management is available in school workspaces")
    return org


def _member_department(role: str) -> str:
    return {
        "teacher": "Teaching & learning",
        "accountant": "Accounts",
        "hr": "HR",
        "parent": "Family",
        "school_admin": "Front-office",
        "owner": "School leadership",
        "admin": "School leadership",
        "student": "Learning",
    }.get(role, "Workspace")


def _member_response(member: User) -> MemberResponse:
    return MemberResponse(id=member.id, name=member.name, email=member.email, role=member.role, status=member.status, department=member.department or _member_department(member.role), profile=member.profile_data or {})


def _current_org(db: Session, user: User) -> Organization:
    org = db.get(Organization, user.org_id) if user.org_id else None
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organization for this user")
    return org


def _require_classroom_manager(user: User, db: Session) -> Organization:
    if user.role not in {"owner", "school_admin", "admin"} or not user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only an owner or school admin can manage classrooms")
    return _current_org(db, user)


def _managed_classroom_response(classroom: Classroom) -> ManagedClassroomResponse:
    students = sorted((link.student for link in classroom.students), key=lambda student: student.name.lower())
    return ManagedClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        subject=_subject_response(classroom.subject),
        teacher=ClassroomMemberResponse(id=classroom.teacher.id, name=classroom.teacher.name),
        students=[ClassroomMemberResponse(id=student.id, name=student.name) for student in students],
    )


def _org_teacher(db: Session, org_id: int, teacher_id: int) -> Teacher:
    teacher = db.get(Teacher, teacher_id)
    user = db.scalar(select(User).where(User.org_id == org_id, User.role == "teacher", User.teacher_id == teacher_id))
    if not teacher or not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found in this organization")
    return teacher


def _org_subject(db: Session, org_id: int, subject_id: int) -> Subject:
    subject = db.get(Subject, subject_id)
    if not subject or subject.org_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found in this organization")
    return subject


def _org_student(db: Session, org_id: int, student_id: int) -> Student:
    student = db.get(Student, student_id)
    member = db.scalar(select(User.id).where(User.org_id == org_id, User.role == "student", User.student_id == student_id))
    admission = db.scalar(select(AdmissionApplication.id).where(AdmissionApplication.org_id == org_id, AdmissionApplication.student_id == student_id))
    if not student or (not member and not admission):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this organization")
    return student


def _student_options(db: Session, org_id: int) -> list[ClassroomMemberResponse]:
    members = db.scalars(
        select(User)
        .where(User.org_id == org_id, User.role == "student", User.student_id.is_not(None))
        .order_by(User.name)
    ).all()
    admission_students = db.scalars(
        select(Student)
        .join(AdmissionApplication, AdmissionApplication.student_id == Student.id)
        .where(AdmissionApplication.org_id == org_id)
        .order_by(Student.name)
    ).all()
    known_student_ids = {member.student_id for member in members}
    return [
        ClassroomMemberResponse(
            id=member.student_id,
            name=member.name or db.get(Student, member.student_id).name,
        )
        for member in members
        if member.student_id
    ] + [
        ClassroomMemberResponse(id=student.id, name=student.name)
        for student in admission_students
        if student.id not in known_student_ids
    ]


@app.get("/api/classrooms", response_model=list[ManagedClassroomResponse])
def list_classrooms(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ManagedClassroomResponse]:
    org = _require_classroom_manager(current_user, db)
    classrooms = db.scalars(select(Classroom).where(Classroom.org_id == org.id).order_by(Classroom.name)).all()
    return [_managed_classroom_response(classroom) for classroom in classrooms]


@app.get("/api/classrooms/options", response_model=ClassroomOptionsResponse)
def classroom_options(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ClassroomOptionsResponse:
    org = _require_classroom_manager(current_user, db)
    subjects = db.scalars(select(Subject).where(Subject.org_id == org.id).order_by(Subject.name)).all()
    teachers = db.scalars(select(User).where(User.org_id == org.id, User.role == "teacher", User.teacher_id.is_not(None)).order_by(User.name)).all()
    return ClassroomOptionsResponse(
        subjects=[_subject_response(subject) for subject in subjects],
        teachers=[ClassroomMemberResponse(id=user.teacher_id, name=db.get(Teacher, user.teacher_id).name) for user in teachers if user.teacher_id],
        students=_student_options(db, org.id),
    )


@app.post("/api/classrooms", response_model=ManagedClassroomResponse, status_code=status.HTTP_201_CREATED)
def create_classroom(payload: ClassroomCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ManagedClassroomResponse:
    org = _require_classroom_manager(current_user, db)
    classroom = Classroom(name=payload.name.strip(), org_id=org.id, subject_id=_org_subject(db, org.id, payload.subject_id).id, teacher_id=_org_teacher(db, org.id, payload.teacher_id).id)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return _managed_classroom_response(classroom)


@app.patch("/api/classrooms/{classroom_id}", response_model=ManagedClassroomResponse)
def update_classroom(classroom_id: int, payload: ClassroomUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ManagedClassroomResponse:
    org = _require_classroom_manager(current_user, db)
    classroom = db.get(Classroom, classroom_id)
    if not classroom or classroom.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    classroom.name = payload.name.strip()
    classroom.subject_id = _org_subject(db, org.id, payload.subject_id).id
    classroom.teacher_id = _org_teacher(db, org.id, payload.teacher_id).id
    db.commit()
    db.refresh(classroom)
    return _managed_classroom_response(classroom)


@app.delete("/api/classrooms/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(classroom_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    org = _require_classroom_manager(current_user, db)
    classroom = db.get(Classroom, classroom_id)
    if not classroom or classroom.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    db.delete(classroom)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/classrooms/{classroom_id}/students", response_model=ManagedClassroomResponse)
def enroll_classroom_student(classroom_id: int, payload: ClassroomEnrollmentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ManagedClassroomResponse:
    org = _require_classroom_manager(current_user, db)
    classroom = db.get(Classroom, classroom_id)
    if not classroom or classroom.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    student = _org_student(db, org.id, payload.student_id)
    if not db.scalar(select(ClassroomStudent.id).where(ClassroomStudent.classroom_id == classroom.id, ClassroomStudent.student_id == student.id)):
        db.add(ClassroomStudent(classroom_id=classroom.id, student_id=student.id))
        db.commit()
        db.refresh(classroom)
    return _managed_classroom_response(classroom)


@app.delete("/api/classrooms/{classroom_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_classroom_student(classroom_id: int, student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    org = _require_classroom_manager(current_user, db)
    classroom = db.get(Classroom, classroom_id)
    if not classroom or classroom.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    enrollment = db.scalar(select(ClassroomStudent).where(ClassroomStudent.classroom_id == classroom.id, ClassroomStudent.student_id == student_id))
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student is not enrolled in this classroom")
    db.delete(enrollment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DashboardResponse:
    if current_user.role == "platform_admin":
        counts = [
            int(db.scalar(select(func.count(Organization.id))) or 0),
            int(db.scalar(select(func.count(User.id))) or 0),
            int(db.scalar(select(func.count(Student.id))) or 0),
        ]
        return DashboardResponse(
            role=current_user.role,
            title="Platform overview",
            metrics=[DashboardMetricResponse(label=label, value=str(value)) for label, value in zip(["Organizations", "Users", "Students"], counts)],
            chart=DashboardChartResponse(label="Platform records", labels=["Organizations", "Users", "Students"], values=counts),
        )

    if current_user.role == "parent":
        children = list_children(current_user=current_user, db=db)
        return DashboardResponse(
            role=current_user.role,
            title="Family overview",
            metrics=[DashboardMetricResponse(label="Children linked", value=str(len(children)))],
            chart=DashboardChartResponse(label="Current mastery", labels=[child.name for child in children], values=[round((child.average_mastery or 0) * 100, 1) for child in children]),
        )

    if current_user.role == "student" and current_user.student_id:
        progress = student_progress(current_user=current_user, db=db)
        return DashboardResponse(
            role=current_user.role,
            title="Learning overview",
            metrics=[
                DashboardMetricResponse(label="Topics", value=str(progress.summary.concept_count)),
                DashboardMetricResponse(label="Mastered", value=str(progress.summary.mastered_count)),
                DashboardMetricResponse(label="Average mastery", value=f"{round(progress.summary.average_effective_mastery * 100)}%"),
            ],
            chart=DashboardChartResponse(label="Mastery by topic", labels=[concept.concept_title for concept in progress.concepts], values=[round(concept.effective_mastery * 100, 1) for concept in progress.concepts]),
        )

    if current_user.role == "teacher" and current_user.teacher_id:
        classrooms = db.scalars(select(Classroom).where(Classroom.teacher_id == current_user.teacher_id).order_by(Classroom.name)).all()
        student_counts = [len(classroom.students) for classroom in classrooms]
        risks = [
            int(
                db.scalar(
                    select(func.count(ForecastRecord.id)).where(
                        ForecastRecord.student_id.in_(
                            select(ClassroomStudent.student_id).where(ClassroomStudent.classroom_id == classroom.id)
                        ),
                        ForecastRecord.predicted_difficulty >= 0.6,
                    )
                )
                or 0
            )
            for classroom in classrooms
        ]
        return DashboardResponse(
            role=current_user.role,
            title="Teaching overview",
            metrics=[
                DashboardMetricResponse(label="My classrooms", value=str(len(classrooms))),
                DashboardMetricResponse(label="Students", value=str(sum(student_counts))),
                DashboardMetricResponse(label="Forecast risks", value=str(sum(risks))),
            ],
            chart=DashboardChartResponse(label="Students by classroom", labels=[classroom.name for classroom in classrooms], values=student_counts),
            classrooms=[_managed_classroom_response(classroom) for classroom in classrooms],
        )

    if current_user.role in {"accountant", "hr"}:
        org = _current_org(db, current_user)
        member_count = int(db.scalar(select(func.count(User.id)).where(User.org_id == org.id)) or 0)
        classroom_count = int(db.scalar(select(func.count(Classroom.id)).where(Classroom.org_id == org.id)) or 0)
        return DashboardResponse(
            role=current_user.role,
            title="Workspace overview",
            metrics=[DashboardMetricResponse(label="Organization", value=org.name), DashboardMetricResponse(label="Members", value=str(member_count)), DashboardMetricResponse(label="Classrooms", value=str(classroom_count))],
            chart=DashboardChartResponse(label="Organization records", labels=["Members", "Classrooms"], values=[member_count, classroom_count]),
        )

    org = _require_org_admin(current_user) or _current_org(db, current_user)
    classrooms = db.scalars(select(Classroom).where(Classroom.org_id == org.id).order_by(Classroom.name)).all()
    students = int(db.scalar(select(func.count(User.id)).where(User.org_id == org.id, User.role == "student")) or 0)
    staff = int(db.scalar(select(func.count(User.id)).where(User.org_id == org.id, User.role.in_(("teacher", "school_admin", "accountant", "hr")))) or 0)
    invoices = db.scalars(select(Invoice).where(Invoice.org_id == org.id, Invoice.voided.is_(False))).all()
    collected = sum(int(db.scalar(select(func.sum(Payment.amount_cents)).where(Payment.invoice_id == invoice.id)) or 0) for invoice in invoices)
    outstanding = sum(max(0, invoice.amount_cents - int(db.scalar(select(func.sum(Payment.amount_cents)).where(Payment.invoice_id == invoice.id)) or 0)) for invoice in invoices)
    admissions = [int(db.scalar(select(func.count(AdmissionApplication.id)).where(AdmissionApplication.org_id == org.id, AdmissionApplication.status == status_value)) or 0) for status_value in ("applied", "reviewing", "accepted", "enrolled")]
    return DashboardResponse(
        role=current_user.role,
        title="School overview",
        metrics=[
            DashboardMetricResponse(label="Students", value=str(students)),
            DashboardMetricResponse(label="Staff", value=str(staff)),
            DashboardMetricResponse(label="Collected", value=f"INR {collected / 100:,.0f}"),
            DashboardMetricResponse(label="Outstanding", value=f"INR {outstanding / 100:,.0f}"),
        ],
        chart=DashboardChartResponse(label="Admissions funnel", labels=["Applied", "Reviewing", "Accepted", "Enrolled"], values=admissions),
        classrooms=[_managed_classroom_response(classroom) for classroom in classrooms],
    )


def _plan_response(plan: Plan) -> PlanResponse:
    return PlanResponse(
        code=plan.code, name=plan.name, segment=plan.segment, price_cents=plan.price_cents, limits=plan.limits or {}, features=list(plan.features or [])
    )


def _org_usage(db: Session, org_id: int) -> OrgUsageResponse:
    members = db.scalar(select(func.count(User.id)).where(User.org_id == org_id)) or 0
    students = db.scalar(select(func.count(User.id)).where(User.org_id == org_id, User.role == "student")) or 0
    classrooms = db.scalar(select(func.count(Classroom.id)).where(Classroom.org_id == org_id)) or 0
    return OrgUsageResponse(members=int(members), students=int(students), classrooms=int(classrooms))


def _org_subscription(db: Session, org_id: int) -> Subscription | None:
    return db.scalar(select(Subscription).where(Subscription.org_id == org_id))


@app.get("/api/org", response_model=OrgResponse)
def get_org(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> OrgResponse:
    _require_org_admin(current_user)
    org = _current_org(db, current_user)
    subscription = _org_subscription(db, org.id)
    sub_response = None
    if subscription:
        plan = db.get(Plan, subscription.plan_id)
        sub_response = SubscriptionResponse(status=subscription.status, plan=_plan_response(plan) if plan else None)
    return OrgResponse(
        id=org.id, name=org.name, slug=org.slug, segment=org.segment, subscription=sub_response, usage=_org_usage(db, org.id)
    )


@app.get("/api/org/members", response_model=MembersResponse)
def list_org_members(q: str = "", offset: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MembersResponse:
    _require_school_owner(current_user, db)
    statement = select(User).where(User.org_id == current_user.org_id)
    if q.strip():
        pattern = f"%{q.strip()}%"
        statement = statement.where(or_(User.name.ilike(pattern), User.email.ilike(pattern), User.role.ilike(pattern)))
    members = db.scalars(statement.order_by(User.id).offset(max(0, offset)).limit(max(1, min(limit, 200)))).all()
    pending = db.scalars(
        select(Invitation).where(Invitation.org_id == current_user.org_id, Invitation.accepted_at.is_(None)).order_by(Invitation.id)
    ).all()
    return MembersResponse(
        members=[_member_response(m) for m in members],
        pending=[PendingInvitationResponse(id=p.id, email=p.email, role=p.role, department=p.department) for p in pending],
    )


@app.post("/api/org/members/{user_id}/role", response_model=MemberResponse)
def change_member_role(user_id: int, payload: ChangeRoleRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MemberResponse:
    _require_school_owner(current_user, db)
    member = db.get(User, user_id)
    if not member or member.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The owner's role cannot be changed")
    if member.role in ("teacher", "student") or payload.role in ("teacher", "student"):
        # profile-linked roles are provisioned at signup/invite; don't remap them here
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher/student roles are set at invitation time")
    member.role = payload.role
    db.commit()
    db.refresh(member)
    return _member_response(member)


@app.patch("/api/org/members/{user_id}/status", response_model=MemberResponse)
def change_member_status(user_id: int, payload: ChangeMemberStatusRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MemberResponse:
    _require_school_owner(current_user, db)
    member = db.get(User, user_id)
    if not member or member.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.id == current_user.id or member.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The owner account cannot be deactivated here")
    member.status = payload.status
    db.commit()
    db.refresh(member)
    return _member_response(member)


@app.patch("/api/org/members/{user_id}/department", response_model=MemberResponse)
def change_member_department(user_id: int, payload: ChangeMemberDepartmentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MemberResponse:
    _require_school_owner(current_user, db)
    if payload.department not in DEPARTMENTS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose a valid department")
    member = db.get(User, user_id)
    if not member or member.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The owner department cannot be changed")
    member.department = payload.department
    _audit(db, current_user, "member.department_changed", member.email, {"department": member.department})
    db.commit(); db.refresh(member)
    return _member_response(member)


@app.delete("/api/org/members/{user_id}", response_model=MemberResponse)
def remove_member(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MemberResponse:
    _require_school_owner(current_user, db)
    member = db.get(User, user_id)
    if not member or member.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.id == current_user.id or member.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The owner account cannot be removed")
    member.status = "inactive"
    _audit(db, current_user, "member.removed", member.email)
    db.commit(); db.refresh(member)
    return _member_response(member)


@app.get("/api/org/members/export.csv")
def export_members_csv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    _require_school_owner(current_user, db)
    members = db.scalars(select(User).where(User.org_id == current_user.org_id).order_by(User.id)).all()
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(["Name", "Email", "Role", "Department", "Status"])
    for member in members:
        writer.writerow([member.name or "", member.email, member.role, _member_department(member.role), member.status])
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=slate-members.csv"})


@app.get("/api/plans", response_model=list[PlanResponse])
def list_plans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PlanResponse]:
    _require_org_admin(current_user)
    org = _current_org(db, current_user)
    plans = db.scalars(select(Plan).where(Plan.segment == org.segment).order_by(Plan.id)).all()
    return [_plan_response(p) for p in plans]


@app.post("/api/org/subscription", response_model=SubscriptionResponse)
def change_subscription(payload: ChangePlanRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SubscriptionResponse:
    if current_user.role not in OWNER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can change the plan")
    org = _current_org(db, current_user)
    plan = db.scalar(select(Plan).where(Plan.code == payload.plan_code))
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    if plan.segment != org.segment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That plan is for a different segment")
    subscription = _org_subscription(db, org.id)
    if subscription:
        subscription.plan_id = plan.id
        subscription.status = "active"
    else:
        subscription = Subscription(org_id=org.id, plan_id=plan.id, status="active")
        db.add(subscription)
    db.commit()
    return SubscriptionResponse(status="active", plan=_plan_response(plan))


def _org_features(db: Session, org_id: int | None) -> list[str]:
    subscription = _org_subscription(db, org_id) if org_id else None
    plan = db.get(Plan, subscription.plan_id) if subscription else None
    return list(plan.features or []) if plan else []


def _require_module(db: Session, user: User, module: str) -> None:
    if module not in _org_features(db, user.org_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Your plan does not include the {module} module")


def _application_response(app_row: AdmissionApplication) -> ApplicationResponse:
    return ApplicationResponse(
        id=app_row.id,
        applicant_name=app_row.applicant_name,
        applicant_email=app_row.applicant_email,
        grade=app_row.grade,
        source=app_row.source,
        date_of_birth=app_row.date_of_birth,
        notes=app_row.notes,
        status=app_row.status,
        student_id=app_row.student_id,
        created_at=app_row.created_at,
        updated_at=app_row.updated_at,
    )


def _owned_application(db: Session, user: User, application_id: int) -> AdmissionApplication:
    _require_org_admin(user)
    _require_module(db, user, "admissions")
    application = db.get(AdmissionApplication, application_id)
    if not application or application.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application


@app.get("/api/admissions/applications", response_model=list[ApplicationResponse])
def list_applications(q: str = "", status_filter: str | None = None, offset: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ApplicationResponse]:
    _require_org_admin(current_user)
    _require_module(db, current_user, "admissions")
    statement = select(AdmissionApplication).where(AdmissionApplication.org_id == current_user.org_id)
    if q.strip():
        pattern = f"%{q.strip()}%"; statement = statement.where(or_(AdmissionApplication.applicant_name.ilike(pattern), AdmissionApplication.applicant_email.ilike(pattern)))
    if status_filter: statement = statement.where(AdmissionApplication.status == status_filter)
    rows = db.scalars(statement.order_by(AdmissionApplication.id.desc()).offset(max(0, offset)).limit(max(1, min(limit, 200)))).all()
    return [_application_response(row) for row in rows]


@app.post("/api/admissions/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationResponse:
    _require_org_admin(current_user)
    _require_module(db, current_user, "admissions")
    application = AdmissionApplication(
        org_id=current_user.org_id,
        applicant_name=payload.applicant_name.strip(),
        applicant_email=(payload.applicant_email or "").strip() or None,
        grade=(payload.grade or "").strip() or None,
        source=(payload.source or "").strip() or None,
        date_of_birth=payload.date_of_birth,
        notes=payload.notes,
        status="applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return _application_response(application)


@app.patch("/api/admissions/applications/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: int, payload: ApplicationCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationResponse:
    application = _owned_application(db, current_user, application_id)
    application.applicant_name = payload.applicant_name.strip()
    application.applicant_email = (payload.applicant_email or "").strip() or None
    application.grade = (payload.grade or "").strip() or None
    application.source = (payload.source or "").strip() or None
    application.date_of_birth = payload.date_of_birth
    application.notes = payload.notes
    db.commit()
    db.refresh(application)
    return _application_response(application)


@app.delete("/api/admissions/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    application = _owned_application(db, current_user, application_id)
    if application.status == "enrolled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enrolled applications must be retained")
    db.delete(application)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/admissions/applications/{application_id}/status", response_model=ApplicationResponse)
def set_application_status(application_id: int, payload: ApplicationStatusRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationResponse:
    application = _owned_application(db, current_user, application_id)
    if application.status == "enrolled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enrolled applications cannot change status")
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return _application_response(application)


@app.post("/api/admissions/applications/{application_id}/enroll", response_model=ApplicationResponse)
def enroll_application(application_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ApplicationResponse:
    application = _owned_application(db, current_user, application_id)
    if application.status != "accepted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application must be accepted before enrolling")

    # Plan gate: enrolled students can't exceed the plan's cap.
    subscription = _org_subscription(db, application.org_id)
    plan = db.get(Plan, subscription.plan_id) if subscription else None
    max_students = (plan.limits or {}).get("max_students") if plan else None
    if isinstance(max_students, int):
        enrolled = db.scalar(
            select(func.count(AdmissionApplication.id)).where(
                AdmissionApplication.org_id == application.org_id, AdmissionApplication.status == "enrolled"
            )
        ) or 0
        if enrolled >= max_students:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Your plan allows {max_students} enrolled students. Upgrade to enroll more.")

    student = Student(name=application.applicant_name.strip(), date_of_birth=application.date_of_birth)
    db.add(student)
    db.flush()
    application.student_id = student.id
    application.status = "enrolled"

    classroom = db.scalar(select(Classroom).where(Classroom.org_id == application.org_id).order_by(Classroom.id))
    if classroom:
        db.add(ClassroomStudent(classroom_id=classroom.id, student_id=student.id))
    if application.applicant_email:
        organization = db.get(Organization, application.org_id)
        create_invitation(db, organization, current_user, application.applicant_email, "student")

    db.commit()
    db.refresh(application)
    return _application_response(application)


FEES_ROLES = {"owner", "school_admin", "accountant", "admin"}
HR_ROLES = {"owner", "school_admin", "hr", "admin"}


def _require_roles(user: User, roles: set[str]) -> None:
    if user.role not in roles or not user.org_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this module")


# ---- M8: Fees & accounting ----


def _paid_cents_map(db: Session, org_id: int) -> dict[int, int]:
    rows = db.execute(
        select(Payment.invoice_id, func.sum(Payment.amount_cents)).where(Payment.org_id == org_id).group_by(Payment.invoice_id)
    ).all()
    return {invoice_id: int(total or 0) for invoice_id, total in rows}


def _invoice_status(amount_cents: int, paid_cents: int, voided: bool) -> str:
    if voided:
        return "void"
    if amount_cents == 0 or paid_cents >= amount_cents:
        return "paid"
    if paid_cents > 0:
        return "partial"
    return "unpaid"


def _invoice_response(db: Session, invoice: Invoice, paid_cents: int) -> InvoiceResponse:
    return InvoiceResponse(
        id=invoice.id,
        student_id=invoice.student_id,
        recipient_name=invoice.recipient_name,
        description=invoice.description,
        amount_cents=invoice.amount_cents,
        paid_cents=paid_cents,
        status=_invoice_status(invoice.amount_cents, paid_cents, invoice.voided),
        voided=invoice.voided,
        due_date=invoice.due_date,
        line_items=[InvoiceLineItemResponse(id=item.id, description=item.description, amount_cents=item.amount_cents) for item in db.scalars(select(InvoiceLineItem).where(InvoiceLineItem.invoice_id == invoice.id).order_by(InvoiceLineItem.id)).all()],
        created_at=invoice.created_at,
    )


def _owned_invoice(db: Session, user: User, invoice_id: int) -> Invoice:
    _require_roles(user, FEES_ROLES)
    _require_module(db, user, "accounting")
    invoice = db.get(Invoice, invoice_id)
    if not invoice or invoice.org_id != user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@app.get("/api/fees/structures", response_model=list[FeeStructureResponse])
def list_fee_structures(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[FeeStructureResponse]:
    _require_roles(current_user, FEES_ROLES)
    _require_module(db, current_user, "accounting")
    rows = db.scalars(select(FeeStructure).where(FeeStructure.org_id == current_user.org_id).order_by(FeeStructure.id)).all()
    return [FeeStructureResponse(id=r.id, name=r.name, amount_cents=r.amount_cents) for r in rows]


@app.get("/api/fees/students/options", response_model=list[ClassroomMemberResponse])
def fee_student_options(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ClassroomMemberResponse]:
    _require_roles(current_user, FEES_ROLES)
    _require_module(db, current_user, "accounting")
    return _student_options(db, current_user.org_id or 0)


@app.post("/api/fees/structures", response_model=FeeStructureResponse, status_code=status.HTTP_201_CREATED)
def create_fee_structure(payload: FeeStructureCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FeeStructureResponse:
    _require_roles(current_user, FEES_ROLES)
    _require_module(db, current_user, "accounting")
    structure = FeeStructure(org_id=current_user.org_id, name=payload.name.strip(), amount_cents=payload.amount_cents)
    db.add(structure)
    db.commit()
    db.refresh(structure)
    return FeeStructureResponse(id=structure.id, name=structure.name, amount_cents=structure.amount_cents)


@app.get("/api/fees/invoices", response_model=list[InvoiceResponse])
def list_invoices(q: str = "", offset: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[InvoiceResponse]:
    _require_roles(current_user, FEES_ROLES)
    _require_module(db, current_user, "accounting")
    statement = select(Invoice).where(Invoice.org_id == current_user.org_id)
    if q.strip(): statement = statement.where(Invoice.recipient_name.ilike(f"%{q.strip()}%"))
    invoices = db.scalars(statement.order_by(Invoice.id.desc()).offset(max(0, offset)).limit(max(1, min(limit, 200)))).all()
    paid = _paid_cents_map(db, current_user.org_id)
    return [_invoice_response(db, inv, paid.get(inv.id, 0)) for inv in invoices]


@app.post("/api/fees/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InvoiceResponse:
    _require_roles(current_user, FEES_ROLES)
    _require_module(db, current_user, "accounting")
    if payload.student_id is not None:
        _org_student(db, current_user.org_id or 0, payload.student_id)
    line_total = sum(item.amount_cents for item in payload.line_items)
    if payload.line_items and line_total != payload.amount_cents:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invoice total must equal the sum of its line items")
    invoice = Invoice(
        org_id=current_user.org_id,
        student_id=payload.student_id,
        recipient_name=payload.recipient_name.strip(),
        description=(payload.description or "").strip() or None,
        amount_cents=payload.amount_cents,
        due_date=payload.due_date,
    )
    db.add(invoice)
    db.flush()
    for item in payload.line_items:
        db.add(InvoiceLineItem(invoice_id=invoice.id, description=item.description.strip(), amount_cents=item.amount_cents))
    db.commit()
    db.refresh(invoice)
    return _invoice_response(db, invoice, 0)


@app.patch("/api/fees/invoices/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: int, payload: InvoiceCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InvoiceResponse:
    invoice = _owned_invoice(db, current_user, invoice_id)
    if invoice.voided or db.scalar(select(func.count(Payment.id)).where(Payment.invoice_id == invoice.id)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only unpaid active invoices can be edited")
    if payload.student_id is not None:
        _org_student(db, current_user.org_id or 0, payload.student_id)
    line_total = sum(item.amount_cents for item in payload.line_items)
    if payload.line_items and line_total != payload.amount_cents:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invoice total must equal the sum of its line items")
    invoice.student_id = payload.student_id
    invoice.recipient_name = payload.recipient_name.strip()
    invoice.description = (payload.description or "").strip() or None
    invoice.amount_cents = payload.amount_cents
    invoice.due_date = payload.due_date
    for item in db.scalars(select(InvoiceLineItem).where(InvoiceLineItem.invoice_id == invoice.id)).all():
        db.delete(item)
    for item in payload.line_items:
        db.add(InvoiceLineItem(invoice_id=invoice.id, description=item.description.strip(), amount_cents=item.amount_cents))
    db.commit()
    db.refresh(invoice)
    return _invoice_response(db, invoice, 0)


@app.post("/api/fees/invoices/{invoice_id}/payments", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def record_payment(invoice_id: int, payload: PaymentCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InvoiceResponse:
    invoice = _owned_invoice(db, current_user, invoice_id)
    if invoice.voided:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot record a payment against a voided invoice")
    db.add(Payment(org_id=invoice.org_id, invoice_id=invoice.id, amount_cents=payload.amount_cents, method=payload.method, note=payload.note))
    db.commit()
    paid = db.scalar(select(func.sum(Payment.amount_cents)).where(Payment.invoice_id == invoice.id)) or 0
    return _invoice_response(db, invoice, int(paid))


@app.post("/api/fees/invoices/{invoice_id}/void", response_model=InvoiceResponse)
def void_invoice(invoice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InvoiceResponse:
    invoice = _owned_invoice(db, current_user, invoice_id)
    invoice.voided = True
    db.commit()
    paid = db.scalar(select(func.sum(Payment.amount_cents)).where(Payment.invoice_id == invoice.id)) or 0
    return _invoice_response(db, invoice, int(paid))


@app.get("/api/fees/summary", response_model=FeesSummaryResponse)
def fees_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FeesSummaryResponse:
    _require_roles(current_user, FEES_ROLES)
    _require_module(db, current_user, "accounting")
    invoices = db.scalars(select(Invoice).where(Invoice.org_id == current_user.org_id, Invoice.voided.is_(False))).all()
    paid = _paid_cents_map(db, current_user.org_id)
    billed = sum(inv.amount_cents for inv in invoices)
    collected = sum(min(paid.get(inv.id, 0), inv.amount_cents) for inv in invoices)
    return FeesSummaryResponse(billed_cents=billed, collected_cents=collected, outstanding_cents=max(0, billed - collected), invoice_count=len(invoices))


# ---- M9: HR & payroll ----


@app.get("/api/hr/employees", response_model=list[EmployeeResponse])
def list_employees(q: str = "", offset: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[EmployeeResponse]:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    statement = select(Employee).where(Employee.org_id == current_user.org_id)
    if q.strip():
        pattern = f"%{q.strip()}%"; statement = statement.where(or_(Employee.name.ilike(pattern), Employee.email.ilike(pattern), Employee.designation.ilike(pattern)))
    rows = db.scalars(statement.order_by(Employee.id).offset(max(0, offset)).limit(max(1, min(limit, 200)))).all()
    return [EmployeeResponse(id=e.id, name=e.name, email=e.email, designation=e.designation, phone=e.phone, join_date=e.join_date, salary_cents=e.salary_cents, status=e.status) for e in rows]


@app.post("/api/hr/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> EmployeeResponse:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    employee = Employee(
        org_id=current_user.org_id,
        name=payload.name.strip(),
        email=(payload.email or "").strip() or None,
        designation=(payload.designation or "").strip() or None,
        phone=(payload.phone or "").strip() or None,
        join_date=payload.join_date,
        salary_cents=payload.salary_cents,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return EmployeeResponse(id=employee.id, name=employee.name, email=employee.email, designation=employee.designation, phone=employee.phone, join_date=employee.join_date, salary_cents=employee.salary_cents, status=employee.status)


@app.patch("/api/hr/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, payload: EmployeeCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> EmployeeResponse:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    employee = db.get(Employee, employee_id)
    if not employee or employee.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    employee.name = payload.name.strip()
    employee.email = (payload.email or "").strip() or None
    employee.designation = (payload.designation or "").strip() or None
    employee.phone = (payload.phone or "").strip() or None
    employee.join_date = payload.join_date
    employee.salary_cents = payload.salary_cents
    db.commit()
    db.refresh(employee)
    return EmployeeResponse(id=employee.id, name=employee.name, email=employee.email, designation=employee.designation, phone=employee.phone, join_date=employee.join_date, salary_cents=employee.salary_cents, status=employee.status)


@app.post("/api/hr/employees/{employee_id}/status", response_model=EmployeeResponse)
def set_employee_status(employee_id: int, payload: EmployeeStatusRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> EmployeeResponse:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    employee = db.get(Employee, employee_id)
    if not employee or employee.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    employee.status = payload.status
    db.commit()
    db.refresh(employee)
    return EmployeeResponse(id=employee.id, name=employee.name, email=employee.email, designation=employee.designation, salary_cents=employee.salary_cents, status=employee.status)


@app.get("/api/hr/payroll", response_model=list[PayrollRunResponse])
def list_payroll_runs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[PayrollRunResponse]:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    runs = db.scalars(select(PayrollRun).where(PayrollRun.org_id == current_user.org_id).order_by(PayrollRun.id.desc())).all()
    result = []
    for run in runs:
        slips = db.scalars(select(Payslip).where(Payslip.payroll_run_id == run.id)).all()
        result.append(
            PayrollRunResponse(
                id=run.id, period=run.period, status=run.status, payslip_count=len(slips), total_net_cents=sum(s.net_cents for s in slips), created_at=run.created_at
            )
        )
    return result


@app.post("/api/hr/payroll", response_model=PayrollRunDetailResponse, status_code=status.HTTP_201_CREATED)
def create_payroll_run(payload: PayrollRunCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PayrollRunDetailResponse:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    employees = db.scalars(select(Employee).where(Employee.org_id == current_user.org_id, Employee.status == "active")).all()
    if not employees:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active employees to run payroll for")
    run = PayrollRun(org_id=current_user.org_id, period=payload.period.strip(), status="finalized")
    db.add(run)
    db.flush()
    slips = []
    for employee in employees:
        slip = Payslip(
            org_id=current_user.org_id,
            payroll_run_id=run.id,
            employee_id=employee.id,
            employee_name=employee.name,
            gross_cents=employee.salary_cents,
            net_cents=employee.salary_cents,
        )
        db.add(slip)
        slips.append(slip)
    db.commit()
    return PayrollRunDetailResponse(
        id=run.id,
        period=run.period,
        status=run.status,
        payslips=[PayslipResponse(id=s.id, employee_name=s.employee_name, gross_cents=s.gross_cents, net_cents=s.net_cents) for s in slips],
    )


@app.get("/api/hr/payroll/{run_id}", response_model=PayrollRunDetailResponse)
def get_payroll_run(run_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PayrollRunDetailResponse:
    _require_roles(current_user, HR_ROLES)
    _require_module(db, current_user, "hr")
    run = db.get(PayrollRun, run_id)
    if not run or run.org_id != current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll run not found")
    slips = db.scalars(select(Payslip).where(Payslip.payroll_run_id == run.id).order_by(Payslip.id)).all()
    return PayrollRunDetailResponse(
        id=run.id,
        period=run.period,
        status=run.status,
        payslips=[PayslipResponse(id=s.id, employee_name=s.employee_name, gross_cents=s.gross_cents, net_cents=s.net_cents) for s in slips],
    )


@app.get("/api/hr/payroll/{run_id}/export.csv")
def export_payroll_csv(run_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    run = get_payroll_run(run_id, current_user=current_user, db=db)
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(["Payroll period", "Employee", "Gross", "Net"])
    for slip in run.payslips:
        writer.writerow([run.period, slip.employee_name, slip.gross_cents, slip.net_cents])
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=slate-payroll-{run.period}.csv"})


# ---- M10: Parent portal ----


def _child_summary(db: Session, student: Student) -> ChildSummaryResponse:
    admission = db.scalar(
        select(AdmissionApplication).where(AdmissionApplication.student_id == student.id).order_by(AdmissionApplication.id.desc())
    )
    invoices = db.scalars(select(Invoice).where(Invoice.student_id == student.id, Invoice.voided.is_(False))).all()
    outstanding = 0
    for invoice in invoices:
        paid = db.scalar(select(func.sum(Payment.amount_cents)).where(Payment.invoice_id == invoice.id)) or 0
        outstanding += max(0, invoice.amount_cents - int(paid))
    mastery_rows = db.scalars(select(MasteryRecord.computed_mastery).where(MasteryRecord.student_id == student.id)).all()
    average = round(sum(mastery_rows) / len(mastery_rows), 4) if mastery_rows else None
    return ChildSummaryResponse(
        student_id=student.id,
        name=student.name,
        admission_status=admission.status if admission else None,
        outstanding_cents=outstanding,
        average_mastery=average,
    )


@app.post("/api/family/links", status_code=status.HTTP_201_CREATED)
def link_guardian(payload: GuardianLinkRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    _require_org_admin(current_user)
    _require_module(db, current_user, "parent")
    parent = db.scalar(
        select(User).where(User.org_id == current_user.org_id, User.email == payload.parent_email.strip().lower(), User.role == "parent")
    )
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No parent member with that email in your organization")
    student = db.get(Student, payload.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    existing = db.scalar(select(GuardianLink).where(GuardianLink.parent_user_id == parent.id, GuardianLink.student_id == student.id))
    if not existing:
        db.add(GuardianLink(org_id=current_user.org_id, parent_user_id=parent.id, student_id=student.id))
        db.commit()
    return {"parent_user_id": parent.id, "student_id": student.id}


@app.get("/api/family/children", response_model=list[ChildSummaryResponse])
def list_children(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ChildSummaryResponse]:
    if current_user.role != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only a parent can view their children")
    _require_module(db, current_user, "parent")
    links = db.scalars(select(GuardianLink).where(GuardianLink.parent_user_id == current_user.id)).all()
    summaries: list[ChildSummaryResponse] = []
    for link in links:
        student = db.get(Student, link.student_id)
        if student:
            summaries.append(_child_summary(db, student))
    return summaries


# ---- M11: Platform admin ----


def _require_platform_admin(user: User) -> None:
    if user.role != "platform_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin access required")


@app.get("/api/admin/orgs", response_model=list[AdminOrgResponse])
def admin_list_orgs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AdminOrgResponse]:
    _require_platform_admin(current_user)
    orgs = db.scalars(select(Organization).order_by(Organization.id)).all()
    result = []
    for org in orgs:
        subscription = _org_subscription(db, org.id)
        plan = db.get(Plan, subscription.plan_id) if subscription else None
        member_count = db.scalar(select(func.count(User.id)).where(User.org_id == org.id)) or 0
        result.append(
            AdminOrgResponse(id=org.id, name=org.name, slug=org.slug, segment=org.segment, plan_code=plan.code if plan else None, member_count=int(member_count))
        )
    return result


@app.get("/api/admin/usage", response_model=AdminUsageResponse)
def admin_usage(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AdminUsageResponse:
    _require_platform_admin(current_user)
    count = lambda model: int(db.scalar(select(func.count(model.id))) or 0)  # noqa: E731
    return AdminUsageResponse(
        orgs=count(Organization),
        users=count(User),
        students=count(Student),
        invoices=count(Invoice),
        employees=count(Employee),
        applications=count(AdmissionApplication),
    )


def _require_teacher_classroom(db: Session, user: User, classroom_id: int, action: str) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    if _cross_org(user, classroom):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access another organization")
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
    if _cross_org(user, classroom):
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


# ---- Phase 3: workspace utilities and school operations ----


def _require_school_operations(user: User, db: Session, roles: set[str] | None = None) -> Organization:
    if roles:
        _require_roles(user, roles)
    else:
        _require_org_admin(user)
    org = _current_org(db, user)
    if org.segment != "school":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This module is available in school workspaces")
    return org


def _audit(db: Session, user: User, action: str, target: str, metadata: dict[str, object] | None = None) -> None:
    db.add(AuditLog(org_id=user.org_id, actor_user_id=user.id, action=action, target=target, audit_metadata=metadata or {}))


@app.get("/api/org/settings")
def get_org_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    org = _current_org(db, current_user)
    return {"id": org.id, "name": org.name, "slug": org.slug, "segment": org.segment, "logo_url": org.logo_url, "timezone": org.timezone, "currency": org.currency}


@app.patch("/api/org/settings")
def update_org_settings(payload: OrganizationSettingsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    if current_user.role not in OWNER_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update workspace settings")
    org = _current_org(db, current_user)
    org.name = payload.name.strip()
    org.logo_url = (payload.logo_url or "").strip() or None
    org.timezone = payload.timezone.strip()
    org.currency = payload.currency.upper()
    _audit(db, current_user, "workspace.updated", org.name)
    db.commit()
    return get_org_settings(current_user=current_user, db=db)


@app.get("/api/search")
def global_search(q: str = "", limit: int = 8, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, list[dict[str, object]]]:
    term = q.strip()
    if len(term) < 2:
        return {"results": []}
    limit = max(1, min(limit, 20))
    pattern = f"%{term}%"
    results: list[dict[str, object]] = []
    if current_user.org_id:
        for member in db.scalars(select(User).where(User.org_id == current_user.org_id, or_(User.name.ilike(pattern), User.email.ilike(pattern))).limit(limit)).all():
            results.append({"kind": "Member", "title": member.name or member.email, "subtitle": member.role.replace("_", " "), "href": "/app/settings/members"})
        for student in db.scalars(select(Student).join(User, User.student_id == Student.id).where(User.org_id == current_user.org_id, Student.name.ilike(pattern)).limit(limit)).all():
            results.append({"kind": "Student", "title": student.name, "subtitle": "Learner record", "href": f"/app/students/{student.id}"})
        if current_user.role in FEES_ROLES:
            for invoice in db.scalars(select(Invoice).where(Invoice.org_id == current_user.org_id, Invoice.recipient_name.ilike(pattern)).limit(limit)).all():
                results.append({"kind": "Invoice", "title": invoice.recipient_name, "subtitle": f"Invoice #{invoice.id}", "href": "/app/fees"})
        for classroom in db.scalars(select(Classroom).where(Classroom.org_id == current_user.org_id, Classroom.name.ilike(pattern)).limit(limit)).all():
            results.append({"kind": "Classroom", "title": classroom.name, "subtitle": classroom.subject.name, "href": "/app/teacher"})
    return {"results": results[:limit]}


@app.get("/api/notifications")
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    rows = db.scalars(select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.id.desc()).limit(20)).all()
    return {"unread": sum(1 for row in rows if row.read_at is None), "items": [{"id": row.id, "title": row.title, "body": row.body, "href": row.href, "read": row.read_at is not None, "created_at": row.created_at} for row in rows]}


@app.get("/api/activity")
def activity_feed(limit: int = 30, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    _require_org_admin(current_user)
    rows = db.scalars(select(AuditLog).where(AuditLog.org_id == current_user.org_id).order_by(AuditLog.id.desc()).limit(max(1, min(limit, 100)))).all()
    return [{"id": row.id, "action": row.action, "target": row.target, "created_at": row.created_at, "metadata": row.audit_metadata} for row in rows]


@app.post("/api/notifications/{notification_id}/read")
def read_notification(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    row = db.get(Notification, notification_id)
    if not row or row.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    row.read_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@app.get("/api/fees/export.csv")
def export_invoices_csv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    invoices = list_invoices(current_user=current_user, db=db)
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(["Invoice", "Recipient", "Description", "Amount", "Paid", "Status", "Due date"])
    for invoice in invoices:
        writer.writerow([invoice.id, invoice.recipient_name, invoice.description or "", invoice.amount_cents, invoice.paid_cents, invoice.status, invoice.due_date or ""])
    return Response(stream.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=slate-invoices.csv"})


@app.get("/api/fees/invoices/{invoice_id}/print")
def print_invoice(invoice_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    invoice = _owned_invoice(db, current_user, invoice_id)
    paid = _paid_cents_map(db, invoice.org_id).get(invoice.id, 0)
    org = _current_org(db, current_user)
    body = f"<h1>{org.name}</h1><h2>Invoice #{invoice.id}</h2><p><b>Recipient:</b> {invoice.recipient_name}</p><p>{invoice.description or ''}</p><p><b>Amount:</b> {invoice.amount_cents / 100:.2f} {org.currency}</p><p><b>Paid:</b> {paid / 100:.2f} {org.currency}</p><script>window.print()</script>"
    return Response(body, media_type="text/html")


@app.get("/api/hr/payroll/{run_id}/print")
def print_payroll(run_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    run = get_payroll_run(run_id, current_user=current_user, db=db)
    org = _current_org(db, current_user)
    rows = "".join(f"<tr><td>{slip.employee_name}</td><td>{slip.net_cents / 100:.2f} {org.currency}</td></tr>" for slip in run.payslips)
    return Response(f"<h1>{org.name}</h1><h2>Payroll {run.period}</h2><table><tr><th>Employee</th><th>Net pay</th></tr>{rows}</table><script>window.print()</script>", media_type="text/html")


@app.get("/api/students/{student_id}/report-card")
def student_report_card(student_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    student = _org_student(db, current_user.org_id or 0, student_id)
    linked = current_user.role == "parent" and bool(db.scalar(select(GuardianLink.id).where(GuardianLink.parent_user_id == current_user.id, GuardianLink.student_id == student.id)))
    if current_user.role == "student" and current_user.student_id != student.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this student")
    if current_user.role not in ORG_ADMIN_ROLES | {"teacher", "student", "parent"} or (current_user.role == "parent" and not linked):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this student")
    records = db.execute(select(MasteryRecord, Concept, Chapter).join(Concept, Concept.id == MasteryRecord.concept_id).join(Chapter, Chapter.id == Concept.chapter_id).where(MasteryRecord.student_id == student.id).order_by(Chapter.order, Concept.order)).all()
    invoices = db.scalars(select(Invoice).where(Invoice.student_id == student.id, Invoice.voided.is_(False))).all()
    paid = _paid_cents_map(db, current_user.org_id or 0)
    attendance = db.execute(select(AttendanceRecord.status, func.count(AttendanceRecord.id)).where(AttendanceRecord.org_id == current_user.org_id, AttendanceRecord.student_id == student.id).group_by(AttendanceRecord.status)).all()
    return {"student_id": student.id, "student_name": student.name, "profile": {"roll_number": student.roll_number, "section": student.section, "date_of_birth": student.date_of_birth, "guardian_name": student.guardian_name, "guardian_phone": student.guardian_phone}, "learning": [{"concept": concept.title, "chapter": chapter.title, "mastery": round(effective_mastery(record), 4)} for record, concept, chapter in records], "fees": {"outstanding_cents": sum(max(0, invoice.amount_cents - paid.get(invoice.id, 0)) for invoice in invoices)}, "attendance": {key: value for key, value in attendance}}


@app.get("/api/attendance/classrooms/{classroom_id}")
def list_attendance(classroom_id: int, attendance_date: date = date.today(), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    classroom = _require_teacher_classroom(db, current_user, classroom_id, "view attendance")
    rows = db.scalars(select(AttendanceRecord).where(AttendanceRecord.classroom_id == classroom.id, AttendanceRecord.attendance_date == attendance_date)).all()
    statuses = {row.student_id: row for row in rows}
    return {"date": attendance_date, "classroom_id": classroom.id, "students": [{"id": link.student.id, "name": link.student.name, "status": statuses.get(link.student.id).status if link.student.id in statuses else None, "note": statuses.get(link.student.id).note if link.student.id in statuses else None} for link in classroom.students]}


@app.put("/api/attendance/classrooms/{classroom_id}")
def save_attendance(classroom_id: int, payload: AttendanceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    classroom = _require_teacher_classroom(db, current_user, classroom_id, "record attendance")
    enrolled = {link.student_id for link in classroom.students}
    for entry in payload.entries:
        if entry.student_id not in enrolled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student is not enrolled in this classroom")
        row = db.scalar(select(AttendanceRecord).where(AttendanceRecord.classroom_id == classroom.id, AttendanceRecord.student_id == entry.student_id, AttendanceRecord.attendance_date == payload.attendance_date))
        if row:
            row.status, row.note, row.recorded_by = entry.status, entry.note, current_user.id
        else:
            db.add(AttendanceRecord(org_id=classroom.org_id, classroom_id=classroom.id, student_id=entry.student_id, attendance_date=payload.attendance_date, status=entry.status, note=entry.note, recorded_by=current_user.id))
    _audit(db, current_user, "attendance.recorded", classroom.name, {"date": payload.attendance_date.isoformat(), "count": len(payload.entries)})
    db.commit()
    return {"saved": len(payload.entries)}


@app.get("/api/timetable")
def list_timetable(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    org = _require_school_operations(current_user, db)
    rows = db.scalars(select(TimetableEntry).where(TimetableEntry.org_id == org.id).order_by(TimetableEntry.weekday, TimetableEntry.starts_at)).all()
    return [{"id": row.id, "classroom_id": row.classroom_id, "classroom": db.get(Classroom, row.classroom_id).name, "weekday": row.weekday, "starts_at": row.starts_at, "ends_at": row.ends_at, "room": row.room} for row in rows]


@app.post("/api/timetable", status_code=status.HTTP_201_CREATED)
def create_timetable_entry(payload: TimetableEntryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    org = _require_school_operations(current_user, db)
    classroom = db.get(Classroom, payload.classroom_id)
    if not classroom or classroom.org_id != org.id: raise HTTPException(status_code=404, detail="Classroom not found")
    row = TimetableEntry(org_id=org.id, **payload.model_dump())
    db.add(row); _audit(db, current_user, "timetable.created", classroom.name); db.commit(); db.refresh(row)
    return {"id": row.id}


@app.delete("/api/timetable/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable_entry(entry_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    org = _require_school_operations(current_user, db); row = db.get(TimetableEntry, entry_id)
    if not row or row.org_id != org.id: raise HTTPException(status_code=404, detail="Timetable entry not found")
    db.delete(row); db.commit(); return Response(status_code=204)


@app.get("/api/library")
def list_library(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    org = _require_school_operations(current_user, db)
    books = db.scalars(select(LibraryBook).where(LibraryBook.org_id == org.id).order_by(LibraryBook.title)).all()
    return [{"id": book.id, "title": book.title, "author": book.author, "isbn": book.isbn, "copies_total": book.copies_total, "copies_available": book.copies_total - int(db.scalar(select(func.count(LibraryLoan.id)).where(LibraryLoan.book_id == book.id, LibraryLoan.returned_at.is_(None))) or 0)} for book in books]


@app.post("/api/library", status_code=status.HTTP_201_CREATED)
def create_library_book(payload: LibraryBookRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    org = _require_school_operations(current_user, db); book = LibraryBook(org_id=org.id, **payload.model_dump())
    db.add(book); _audit(db, current_user, "library.book_added", book.title); db.commit(); db.refresh(book); return {"id": book.id}


@app.post("/api/library/{book_id}/loans", status_code=status.HTTP_201_CREATED)
def loan_library_book(book_id: int, payload: LibraryLoanRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    org = _require_school_operations(current_user, db); book = db.get(LibraryBook, book_id)
    if not book or book.org_id != org.id: raise HTTPException(status_code=404, detail="Book not found")
    _org_student(db, org.id, payload.student_id)
    active = int(db.scalar(select(func.count(LibraryLoan.id)).where(LibraryLoan.book_id == book.id, LibraryLoan.returned_at.is_(None))) or 0)
    if active >= book.copies_total: raise HTTPException(status_code=400, detail="No copies available")
    loan = LibraryLoan(org_id=org.id, book_id=book.id, student_id=payload.student_id, due_date=payload.due_date)
    db.add(loan); db.commit(); return {"id": loan.id}


@app.post("/api/library/loans/{loan_id}/return")
def return_library_book(loan_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    org = _require_school_operations(current_user, db); loan = db.get(LibraryLoan, loan_id)
    if not loan or loan.org_id != org.id: raise HTTPException(status_code=404, detail="Loan not found")
    loan.returned_at = datetime.now(timezone.utc); db.commit(); return {"ok": True}


@app.get("/api/transport")
def list_transport_routes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    org = _require_school_operations(current_user, db)
    rows = db.scalars(select(TransportRoute).where(TransportRoute.org_id == org.id).order_by(TransportRoute.name)).all()
    return [{"id": row.id, "name": row.name, "vehicle_label": row.vehicle_label, "driver_name": row.driver_name, "stops": row.stops, "student_count": int(db.scalar(select(func.count(StudentTransportAssignment.id)).where(StudentTransportAssignment.route_id == row.id)) or 0)} for row in rows]


@app.post("/api/transport", status_code=status.HTTP_201_CREATED)
def create_transport_route(payload: TransportRouteRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    org = _require_school_operations(current_user, db); route = TransportRoute(org_id=org.id, **payload.model_dump())
    db.add(route); _audit(db, current_user, "transport.route_created", route.name); db.commit(); db.refresh(route); return {"id": route.id}


@app.put("/api/transport/assignments")
def assign_transport(payload: TransportAssignmentRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, int]:
    org = _require_school_operations(current_user, db); _org_student(db, org.id, payload.student_id)
    route = db.get(TransportRoute, payload.route_id)
    if not route or route.org_id != org.id: raise HTTPException(status_code=404, detail="Route not found")
    assignment = db.scalar(select(StudentTransportAssignment).where(StudentTransportAssignment.student_id == payload.student_id))
    if assignment: assignment.route_id, assignment.stop_name, assignment.org_id = route.id, payload.stop_name, org.id
    else: assignment = StudentTransportAssignment(org_id=org.id, student_id=payload.student_id, route_id=route.id, stop_name=payload.stop_name); db.add(assignment)
    db.commit(); return {"id": assignment.id}
