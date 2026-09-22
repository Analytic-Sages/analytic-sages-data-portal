"""Admin waitlist / access management."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth_users import require_admin
from app.db import get_db
from app.emailer import send_approval_email
from app.models import ACCESS_APPROVED, ACCESS_SUSPENDED, ACCESS_WAITLIST_PENDING, User

router = APIRouter(prefix="/admin/users", tags=["admin-users"], dependencies=[Depends(require_admin)])


class AccessUpdate(BaseModel):
    access_status: str = Field(pattern="^(WAITLIST_PENDING|APPROVED|SUSPENDED)$")
    note: str | None = None


@router.get("")
def list_users(
    access_status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    query = db.query(User).order_by(User.created_at.desc())
    if access_status:
        query = query.filter(User.access_status == access_status)
    if q:
        like = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                User.email.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.phone_number.ilike(like),
                User.country_of_residence.ilike(like),
            )
        )
    users = query.limit(500).all()
    return {"users": [u.to_public_dict() for u in users]}


@router.post("/{user_id}/approve")
def approve_user(user_id: str, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.access_status = ACCESS_APPROVED
    user.email_verified = True
    user.approved_at = datetime.now(timezone.utc)
    user.approved_by = "admin"
    db.commit()
    db.refresh(user)
    send_approval_email(user.email)
    return {"user": user.to_public_dict()}


@router.post("/{user_id}/suspend")
def suspend_user(user_id: str, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.access_status = ACCESS_SUSPENDED
    db.commit()
    db.refresh(user)
    return {"user": user.to_public_dict()}


@router.patch("/{user_id}")
def update_access(user_id: str, body: AccessUpdate, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    prev = user.access_status
    user.access_status = body.access_status
    if body.access_status == ACCESS_APPROVED:
        user.email_verified = True
        user.approved_at = datetime.now(timezone.utc)
        user.approved_by = "admin"
        if prev != ACCESS_APPROVED:
            send_approval_email(user.email)
    elif body.access_status == ACCESS_WAITLIST_PENDING:
        pass
    elif body.access_status == ACCESS_SUSPENDED:
        pass
    db.commit()
    db.refresh(user)
    return {"user": user.to_public_dict()}
