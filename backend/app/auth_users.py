"""User auth helpers: passwords, sessions, access checks."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    ACCESS_APPROVED,
    ACCESS_WAITLIST_PENDING,
    EmailToken,
    SessionToken,
    User,
)

SESSION_COOKIE = "as_portal_session"
SESSION_DAYS = 14


def _pbkdf2(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _pbkdf2(password, salt)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or not stored.startswith("pbkdf2_sha256$"):
        return False
    try:
        _, salt_hex, digest_hex = stored.split("$", 2)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual = _pbkdf2(password, salt)
    return hmac.compare_digest(actual, expected)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def approved_tester_emails() -> set[str]:
    raw = os.environ.get("APPROVED_TESTER_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def admin_emails() -> set[str]:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def user_is_admin(user: User) -> bool:
    return user.email.lower() in admin_emails()


def private_access_mode() -> bool:
    """Allow self-registered accounts to use Query Studio without an invite or waitlist."""
    return True


def invite_only_mode() -> bool:
    """Require a valid invite before creating or recovering an account."""
    return os.environ.get("INVITE_ONLY_MODE", "1").lower() in {"1", "true", "yes"}


def apply_tester_seed(user: User) -> None:
    if user.email.lower() in approved_tester_emails():
        user.is_tester = True
        user.access_status = ACCESS_APPROVED
        user.email_verified = True
        user.approved_at = datetime.now(timezone.utc)
        user.approved_by = "APPROVED_TESTER_EMAILS"


def apply_admin_seed(user: User) -> None:
    if user_is_admin(user):
        user.access_status = ACCESS_APPROVED
        user.email_verified = True
        if user.approved_at is None:
            user.approved_at = datetime.now(timezone.utc)
        if not user.approved_by:
            user.approved_by = "ADMIN_EMAILS"


def apply_access_policy(user: User, db: Session | None = None) -> None:
    """Apply tester allow-list, pending invites, and optional private (no-waitlist) access."""
    apply_tester_seed(user)
    apply_admin_seed(user)
    if db is not None:
        from app.invites import consume_invite_for_user

        consume_invite_for_user(db, user)
    if private_access_mode() and user.access_status != "SUSPENDED":
        user.access_status = ACCESS_APPROVED
        user.email_verified = True
        if user.approved_at is None:
            user.approved_at = datetime.now(timezone.utc)
        if not user.approved_by:
            user.approved_by = "PRIVATE_ACCESS_MODE"


def cookie_secure() -> bool:
    return os.environ.get("COOKIE_SECURE", "0").lower() in {"1", "true", "yes"}


def set_session_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=raw_token,
        httponly=True,
        secure=cookie_secure(),
        samesite="lax",
        max_age=SESSION_DAYS * 24 * 3600,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE, path="/")


def create_session(db: Session, user: User) -> str:
    raw = secrets.token_urlsafe(32)
    row = SessionToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS),
    )
    db.add(row)
    db.commit()
    return raw


def create_email_token(db: Session, user: User, purpose: str, hours: int = 48) -> str:
    raw = secrets.token_urlsafe(32)
    row = EmailToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(raw),
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=hours),
    )
    db.add(row)
    db.commit()
    return raw


def get_user_by_session(db: Session, raw_token: str | None) -> User | None:
    if not raw_token:
        return None
    row = (
        db.query(SessionToken)
        .filter(SessionToken.token_hash == hash_token(raw_token))
        .first()
    )
    if row is None:
        return None
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        return None
    return db.get(User, row.user_id)


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    as_portal_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User | None:
    token = as_portal_session or request.cookies.get(SESSION_COOKIE)
    return get_user_by_session(db, token)


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "EARLY_ACCESS_REQUIRED",
                "message": "Query Studio access requires early access approval.",
            },
        )
    return user


class QueryAccessError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 403) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
        )


def require_query_access(user: User = Depends(get_current_user)) -> User:
    if user.access_status == "SUSPENDED":
        raise QueryAccessError(
            "ACCESS_SUSPENDED",
            "Your Query Studio access has been suspended.",
        )
    if not user.email_verified:
        raise QueryAccessError(
            "EMAIL_VERIFICATION_REQUIRED",
            "Verify your email before using Query Studio.",
        )
    if not user.can_run_queries():
        raise QueryAccessError(
            "WAITLIST_PENDING",
            "Your account is on the early-access waitlist. Query Studio unlocks after approval.",
        )
    return user


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone_country_code: str = "",
    phone_number: str = "",
    country_of_residence: str = "",
    invite_token: str | None = None,
) -> User:
    from app.invites import consume_invite_for_user, find_invite_by_token, is_invite_active

    email_norm = email.strip().lower()
    user = User(
        id=str(uuid.uuid4()),
        email=email_norm,
        password_hash=hash_password(password),
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        phone_country_code=phone_country_code.strip(),
        phone_number=phone_number.strip(),
        country_of_residence=country_of_residence.strip().upper()[:2],
        email_verified=False,
        access_status=ACCESS_WAITLIST_PENDING,
        is_tester=False,
    )
    apply_tester_seed(user)
    apply_admin_seed(user)
    db.add(user)
    db.flush()
    if invite_token:
        invite = find_invite_by_token(db, invite_token)
        if invite is not None and is_invite_active(invite) and invite.email.lower() == email_norm:
            consume_invite_for_user(db, user, raw_token=invite_token)
        else:
            consume_invite_for_user(db, user)
    else:
        consume_invite_for_user(db, user)
    if private_access_mode() and user.access_status != "SUSPENDED":
        user.access_status = ACCESS_APPROVED
        user.email_verified = True
        if user.approved_at is None:
            user.approved_at = datetime.now(timezone.utc)
        if not user.approved_by:
            user.approved_by = "PRIVATE_ACCESS_MODE"
    db.commit()
    db.refresh(user)
    return user


def require_admin(
    request: Request,
    db: Session = Depends(get_db),
    as_portal_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> User | None:
    """Allow admin session cookie, or optional legacy ADMIN_API_KEY header."""
    token = as_portal_session or request.cookies.get(SESSION_COOKIE)
    user = get_user_by_session(db, token)
    if user is not None:
        apply_access_policy(user, db)
        db.commit()
        if user_is_admin(user) and user.access_status != "SUSPENDED":
            return user

    expected = os.environ.get("ADMIN_API_KEY", "")
    if (
        expected
        and x_admin_key
        and len(x_admin_key) == len(expected)
        and hmac.compare_digest(x_admin_key, expected)
    ):
        return None

    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Admin access required."},
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "ADMIN_REQUIRED",
            "message": "Sign in with an admin account to continue.",
        },
    )
