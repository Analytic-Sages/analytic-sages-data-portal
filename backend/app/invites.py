"""Admin invite helpers: create, validate, and consume email invites."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth_users import hash_token
from app.emailer import frontend_origin
from app.models import (
    ACCESS_APPROVED,
    ACCESS_SUSPENDED,
    INVITE_ACCEPTED,
    INVITE_PENDING,
    INVITE_REVOKED,
    Invite,
    User,
)


def invite_url_for_token(raw_token: str) -> str:
    return f"{frontend_origin()}/signup?invite={raw_token}"


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_invite_active(invite: Invite) -> bool:
    if invite.status != INVITE_PENDING:
        return False
    return _aware(invite.expires_at) >= datetime.now(timezone.utc)


def find_invite_by_token(db: Session, raw_token: str) -> Invite | None:
    return (
        db.query(Invite)
        .filter(Invite.token_hash == hash_token(raw_token))
        .order_by(Invite.created_at.desc())
        .first()
    )


def find_pending_invite_for_email(db: Session, email: str) -> Invite | None:
    email_norm = email.strip().lower()
    rows = (
        db.query(Invite)
        .filter(Invite.email == email_norm, Invite.status == INVITE_PENDING)
        .order_by(Invite.created_at.desc())
        .all()
    )
    for row in rows:
        if is_invite_active(row):
            return row
    return None


def approve_user_from_invite(user: User, *, approved_by: str = "invite") -> None:
    if user.access_status == ACCESS_SUSPENDED:
        return
    user.access_status = ACCESS_APPROVED
    user.email_verified = True
    user.approved_at = datetime.now(timezone.utc)
    user.approved_by = approved_by


def mark_invite_accepted(invite: Invite, user: User) -> None:
    invite.status = INVITE_ACCEPTED
    invite.accepted_at = datetime.now(timezone.utc)
    invite.accepted_user_id = user.id


def consume_invite_for_user(
    db: Session,
    user: User,
    *,
    raw_token: str | None = None,
) -> Invite | None:
    """Approve user if a matching active invite exists. Returns the invite if consumed."""
    if user.access_status == ACCESS_SUSPENDED:
        return None

    invite: Invite | None = None
    if raw_token:
        invite = find_invite_by_token(db, raw_token)
        if invite is None or not is_invite_active(invite):
            return None
        if invite.email.lower() != user.email.lower():
            return None
    else:
        invite = find_pending_invite_for_email(db, user.email)

    if invite is None:
        return None

    approve_user_from_invite(user, approved_by="invite")
    mark_invite_accepted(invite, user)
    return invite


def create_invite(
    db: Session,
    *,
    email: str,
    note: str = "",
    days: int = 14,
    invited_by: str = "admin",
) -> tuple[Invite, str]:
    email_norm = email.strip().lower()
    # Close older pending invites for the same email so only one is active.
    for old in (
        db.query(Invite)
        .filter(Invite.email == email_norm, Invite.status == INVITE_PENDING)
        .all()
    ):
        old.status = INVITE_REVOKED

    raw = secrets.token_urlsafe(32)
    invite = Invite(
        id=str(uuid.uuid4()),
        email=email_norm,
        token_hash=hash_token(raw),
        status=INVITE_PENDING,
        note=(note or "").strip()[:500],
        invited_by=invited_by,
        expires_at=datetime.now(timezone.utc) + timedelta(days=max(1, min(days, 90))),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite, raw
