import os
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session

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
from app.models import User

app = FastAPI(title="ConfusionLayer API")


@app.get("/api/health")
def health() -> dict[str, str | bool | int]:
    return {
        "ok": True,
        "service": "confusionlayer-backend",
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "ai_daily_call_limit": int(os.getenv("AI_DAILY_CALL_LIMIT", "50")),
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
