from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import re

from app.db import get_db
from app.mail import send_email
from app.models import Invitation, Organization, PasswordReset, Plan, Student, Subscription, Teacher, User

Role = Literal["admin", "teacher", "student"]
Segment = Literal["school", "institute", "individual"]
# Invitable roles are enforced by the Literal on InvitationCreateRequest.role
# (never owner or platform_admin).
_SEGMENT_DEFAULT_PLAN = {"school": "school_free", "institute": "institute_free", "individual": "individual_free"}
ACCESS_TOKEN_COOKIE = "access_token"
JWT_ALGORITHM = "HS256"
PBKDF2_ITERATIONS = 210_000
bearer_scheme = HTTPBearer(auto_error=False)


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    role: Role
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class DemoLoginRequest(BaseModel):
    role: Literal["teacher", "student"] = "teacher"


class RegisterRequest(BaseModel):
    org_name: str = Field(min_length=1, max_length=160)
    segment: Segment
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=8, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class InvitationCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: Literal["school_admin", "accountant", "hr", "teacher", "student", "parent"]


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=8, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class InvitationPreviewResponse(BaseModel):
    email: str
    role: str
    organization_name: str


class AuthUserResponse(BaseModel):
    id: int
    email: str
    name: str | None = None
    role: str
    org_id: int | None = None
    org_name: str | None = None
    segment: str | None = None
    teacher_id: int | None = None
    student_id: int | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserResponse


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = _b64url_decode(salt_text)
        expected_digest = _b64url_decode(digest_text)
    except (ValueError, TypeError):
        return False

    actual_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(user: User, expires_delta: timedelta | None = None) -> str:
    expires_at = datetime.now(UTC) + (expires_delta or timedelta(hours=_jwt_expiry_hours()))
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": int(expires_at.timestamp()),
    }
    return encode_jwt(payload)


def encode_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    signing_input = f"{_json_b64(header)}.{_json_b64(payload)}"
    signature = hmac.new(_jwt_secret(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        header_text, payload_text, signature_text = token.split(".", 2)
        signing_input = f"{header_text}.{payload_text}"
        expected_signature = hmac.new(_jwt_secret(), signing_input.encode("ascii"), hashlib.sha256).digest()
        actual_signature = _b64url_decode(signature_text)
        if not hmac.compare_digest(actual_signature, expected_signature):
            raise ValueError("bad signature")
        header = json.loads(_b64url_decode(header_text))
        payload = json.loads(_b64url_decode(payload_text))
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from None

    if header.get("alg") != JWT_ALGORITHM:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(UTC).timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token expired")

    return payload


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=_jwt_expiry_hours() * 60 * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE, path="/")


def user_response(user: User, organization: Organization | None = None) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        org_id=user.org_id,
        org_name=organization.name if organization else None,
        segment=organization.segment if organization else None,
        teacher_id=user.teacher_id,
        student_id=user.student_id,
    )


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    token = credentials.credentials if credentials else request.cookies.get(ACCESS_TOKEN_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = decode_jwt(token)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication user not found")
    return user


def create_user(db: Session, payload: SignupRequest) -> User:
    email = normalize_email(payload.email)
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    teacher_id: int | None = None
    student_id: int | None = None
    if payload.role == "teacher":
        teacher = Teacher(name=payload.name.strip())
        db.add(teacher)
        db.flush()
        teacher_id = teacher.id
    elif payload.role == "student":
        student = Student(name=payload.name.strip())
        db.add(student)
        db.flush()
        student_id = student.id

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        teacher_id=teacher_id,
        student_id=student_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_demo_user(db: Session, role: Literal["teacher", "student"]) -> User:
    email = f"demo.{role}@confusionlayer.local"
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return existing

    org = db.scalar(select(Organization).order_by(Organization.id))
    org_id = org.id if org else None
    if role == "teacher":
        teacher = db.scalar(select(Teacher).order_by(Teacher.id))
        if not teacher:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Demo teacher seed data is missing")
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(32)), role="teacher", teacher_id=teacher.id, org_id=org_id)
    else:
        student = db.scalar(select(Student).order_by(Student.id))
        if not student:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Demo student seed data is missing")
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(32)), role="student", student_id=student.id, org_id=org_id)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _is_past(moment: datetime) -> bool:
    # Stored timestamps come back naive on SQLite and tz-aware on Postgres; normalize.
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment < datetime.now(UTC)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "org"


def _unique_org_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug = base
    suffix = 2
    while db.scalar(select(Organization).where(Organization.slug == slug)):
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def register_org(db: Session, payload: RegisterRequest) -> tuple[User, Organization]:
    email = normalize_email(payload.email)
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    plan = db.scalar(select(Plan).where(Plan.code == _SEGMENT_DEFAULT_PLAN[payload.segment]))
    if not plan:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Plans are not configured")

    org = Organization(name=payload.org_name.strip(), slug=_unique_org_slug(db, payload.org_name), segment=payload.segment)
    db.add(org)
    db.flush()
    db.add(Subscription(org_id=org.id, plan_id=plan.id, status="active"))
    user = User(
        org_id=org.id,
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        role="owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(org)
    return user, org


def request_password_reset(db: Session, email: str) -> None:
    # Always behaves the same regardless of whether the email exists (no enumeration).
    user = db.scalar(select(User).where(User.email == normalize_email(email)))
    if not user:
        return
    token = secrets.token_urlsafe(32)
    db.add(PasswordReset(user_id=user.id, token=token, expires_at=datetime.now(UTC) + timedelta(hours=1)))
    db.commit()
    send_email(user.email, "Reset your Slate password", f"Use this link to reset your password: /reset-password/{token}")


def reset_password(db: Session, token: str, new_password: str) -> None:
    reset = db.scalar(select(PasswordReset).where(PasswordReset.token == token))
    if not reset or reset.used_at is not None or _is_past(reset.expires_at):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user = db.get(User, reset.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.password_hash = hash_password(new_password)
    reset.used_at = datetime.now(UTC)
    db.commit()


def create_invitation(db: Session, org: Organization, inviter: User, email: str, role: str) -> Invitation:
    invitation = Invitation(
        org_id=org.id,
        email=normalize_email(email),
        role=role,
        token=secrets.token_urlsafe(32),
        invited_by=inviter.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    send_email(email, f"You're invited to {org.name} on Slate", f"Accept your invite: /accept-invite/{invitation.token}")
    return invitation


def get_open_invitation(db: Session, token: str) -> Invitation:
    invitation = db.scalar(select(Invitation).where(Invitation.token == token))
    if not invitation or invitation.accepted_at is not None or _is_past(invitation.expires_at):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation is invalid or has expired")
    return invitation


def accept_invitation(db: Session, token: str, password: str, name: str) -> tuple[User, Organization]:
    invitation = get_open_invitation(db, token)
    if db.scalar(select(User).where(User.email == invitation.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    teacher_id: int | None = None
    student_id: int | None = None
    if invitation.role == "teacher":
        teacher = Teacher(name=name.strip())
        db.add(teacher)
        db.flush()
        teacher_id = teacher.id
    elif invitation.role == "student":
        student = Student(name=name.strip())
        db.add(student)
        db.flush()
        student_id = student.id

    user = User(
        org_id=invitation.org_id,
        email=invitation.email,
        name=name.strip(),
        password_hash=hash_password(password),
        role=invitation.role,
        teacher_id=teacher_id,
        student_id=student_id,
    )
    db.add(user)
    invitation.accepted_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    organization = db.get(Organization, invitation.org_id)
    return user, organization


def _jwt_secret() -> bytes:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET is required")
    return secret.encode("utf-8")


def _jwt_expiry_hours() -> int:
    return int(os.getenv("JWT_EXPIRES_HOURS", "24"))


def _cookie_secure() -> bool:
    return os.getenv("AUTH_COOKIE_SECURE", "1") != "0"


def _json_b64(value: dict[str, Any]) -> str:
    return _b64url_encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
