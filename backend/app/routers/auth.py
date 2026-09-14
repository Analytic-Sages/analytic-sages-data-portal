"""Signup, login, logout, verify, and password reset."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth_users import (
    SESSION_COOKIE,
    apply_access_policy,
    clear_session_cookie,
    create_email_token,
    create_session,
    create_user,
    get_optional_user,
    hash_password,
    hash_token,
    private_access_mode,
    set_session_cookie,
    verify_password,
)
from app.db import get_db
from app.emailer import send_password_reset_email, send_verification_email
from app.models import EmailToken, SessionToken, User

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenBody(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class ResetBody(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class ForgotBody(BaseModel):
    email: EmailStr


@router.get("/config")
def auth_config() -> dict:
    return {
        "private_access_mode": private_access_mode(),
        "waitlist_enabled": not private_access_mode(),
    }


@router.post("/signup")
def signup(body: SignupBody, response: Response, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_IN_USE", "message": "An account with this email already exists."},
        )
    user = create_user(
        db,
        email=email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    if not user.email_verified:
        raw = create_email_token(db, user, "verify", hours=48)
        send_verification_email(user.email, raw)
    raw_session = create_session(db, user)
    set_session_cookie(response, raw_session)
    return {"user": user.to_public_dict()}


@router.post("/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."},
        )
    apply_access_policy(user)
    db.commit()
    db.refresh(user)
    raw_session = create_session(db, user)
    set_session_cookie(response, raw_session)
    return {"user": user.to_public_dict()}


@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    as_portal_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> dict:
    if as_portal_session:
        db.query(SessionToken).filter(
            SessionToken.token_hash == hash_token(as_portal_session)
        ).delete()
        db.commit()
    clear_session_cookie(response)
    return {"status": "ok"}


@router.get("/me")
def me(db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)) -> dict:
    if user is None:
        return {"user": None}
    apply_access_policy(user)
    db.commit()
    db.refresh(user)
    return {"user": user.to_public_dict()}


@router.post("/verify-email")
def verify_email(body: TokenBody, db: Session = Depends(get_db)) -> dict:
    row = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == hash_token(body.token),
            EmailToken.purpose == "verify",
        )
        .first()
    )
    if row is None or row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "Verification link is invalid or expired."},
        )
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "Verification link is invalid or expired."},
        )
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Invalid token."})
    user.email_verified = True
    row.used_at = datetime.now(timezone.utc)
    apply_access_policy(user)
    db.commit()
    db.refresh(user)
    return {"user": user.to_public_dict()}


@router.post("/forgot-password")
def forgot_password(body: ForgotBody, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    # Always OK to avoid email enumeration
    if user is not None:
        raw = create_email_token(db, user, "reset", hours=2)
        send_password_reset_email(user.email, raw)
    return {"status": "ok", "message": "If that email exists, a reset link was sent."}


@router.post("/reset-password")
def reset_password(body: ResetBody, db: Session = Depends(get_db)) -> dict:
    row = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == hash_token(body.token),
            EmailToken.purpose == "reset",
        )
        .first()
    )
    if row is None or row.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "Reset link is invalid or expired."},
        )
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": "Reset link is invalid or expired."},
        )
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail={"code": "INVALID_TOKEN", "message": "Invalid token."})
    user.password_hash = hash_password(body.password)
    row.used_at = datetime.now(timezone.utc)
    db.query(SessionToken).filter(SessionToken.user_id == user.id).delete()
    db.commit()
    return {"status": "ok"}


@router.post("/resend-verification")
def resend_verification(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> dict:
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "EARLY_ACCESS_REQUIRED", "message": "Sign in required."},
        )
    if user.email_verified:
        return {"status": "ok", "message": "Email already verified."}
    raw = create_email_token(db, user, "verify", hours=48)
    send_verification_email(user.email, raw)
    return {"status": "ok"}
