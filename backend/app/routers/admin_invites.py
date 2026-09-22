"""Admin invite management: grant access by email invite."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.auth_users import require_admin
from app.db import get_db
from app.emailer import send_approval_email, send_invite_email
from app.invites import (
    approve_user_from_invite,
    create_invite,
    invite_url_for_token,
    is_invite_active,
    mark_invite_accepted,
)
from app.models import INVITE_PENDING, INVITE_REVOKED, Invite, User

router = APIRouter(prefix="/admin/invites", tags=["admin-invites"], dependencies=[Depends(require_admin)])


class InviteCreate(BaseModel):
    email: EmailStr
    note: str = Field(default="", max_length=500)
    days: int = Field(default=14, ge=1, le=90)


@router.get("")
def list_invites(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(Invite).order_by(Invite.created_at.desc())
    if status:
        query = query.filter(Invite.status == status.upper())
    invites = query.limit(500).all()
    return {"invites": [i.to_public_dict() for i in invites]}


@router.post("")
def create_invite_endpoint(body: InviteCreate, db: Session = Depends(get_db)) -> dict:
    email = body.email.strip().lower()
    invite, raw = create_invite(
        db,
        email=email,
        note=body.note,
        days=body.days,
        invited_by="admin",
    )
    url = invite_url_for_token(raw)
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        if existing.access_status != "SUSPENDED":
            approve_user_from_invite(existing, approved_by="invite")
            mark_invite_accepted(invite, existing)
            db.commit()
            db.refresh(invite)
            db.refresh(existing)
            send_approval_email(existing.email)
            return {
                "invite": invite.to_public_dict(),
                "invite_url": url,
                "existing_user_approved": True,
                "user": existing.to_public_dict(),
            }
        raise HTTPException(
            status_code=400,
            detail={
                "code": "USER_SUSPENDED",
                "message": "This user is suspended. Unsuspend them before inviting.",
            },
        )

    send_invite_email(email, raw)
    return {
        "invite": invite.to_public_dict(invite_url=url),
        "invite_url": url,
        "existing_user_approved": False,
        "user": None,
    }


@router.post("/{invite_id}/revoke")
def revoke_invite(invite_id: str, db: Session = Depends(get_db)) -> dict:
    invite = db.get(Invite, invite_id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.status == INVITE_PENDING:
        invite.status = INVITE_REVOKED
        db.commit()
        db.refresh(invite)
    return {"invite": invite.to_public_dict()}


@router.post("/{invite_id}/resend")
def resend_invite(invite_id: str, db: Session = Depends(get_db)) -> dict:
    """Revoke the old invite and issue a fresh one for the same email."""
    invite = db.get(Invite, invite_id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    if not is_invite_active(invite) and invite.status != INVITE_PENDING:
        # Allow resend from revoked/accepted-for-wrong-reason by creating new
        pass
    existing = db.query(User).filter(User.email == invite.email).first()
    if existing is not None and existing.access_status == "APPROVED":
        raise HTTPException(
            status_code=400,
            detail={"code": "ALREADY_APPROVED", "message": "User already has access."},
        )
    new_invite, raw = create_invite(
        db,
        email=invite.email,
        note=invite.note,
        days=14,
        invited_by="admin",
    )
    url = invite_url_for_token(raw)
    if existing is not None:
        approve_user_from_invite(existing, approved_by="invite")
        mark_invite_accepted(new_invite, existing)
        db.commit()
        db.refresh(new_invite)
        send_approval_email(existing.email)
        return {
            "invite": new_invite.to_public_dict(),
            "invite_url": url,
            "existing_user_approved": True,
        }
    send_invite_email(invite.email, raw)
    return {
        "invite": new_invite.to_public_dict(invite_url=url),
        "invite_url": url,
        "existing_user_approved": False,
    }
