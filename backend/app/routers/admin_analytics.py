"""Admin analytics summary for the portal operations dashboard."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth_users import require_admin
from app.db import get_db
from app.models import QueryEvent, User
from app.query_policy import load_policy
from app.config import get_settings

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"], dependencies=[Depends(require_admin)])


def _day_key(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


@router.get("/summary")
def analytics_summary(
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    settings = get_settings()

    users = db.query(User).all()
    by_status = Counter(u.access_status for u in users)
    by_country = Counter(
        (u.country_of_residence or "UN").upper() for u in users if (u.country_of_residence or "").strip()
    )
    if not by_country:
        by_country = Counter({"UN": 0})

    signups_by_day: dict[str, int] = defaultdict(int)
    for u in users:
        if u.created_at is None:
            continue
        created = u.created_at if u.created_at.tzinfo else u.created_at.replace(tzinfo=timezone.utc)
        if created >= since:
            signups_by_day[_day_key(created)] += 1

    events = (
        db.query(QueryEvent)
        .filter(QueryEvent.created_at >= since)
        .order_by(QueryEvent.created_at.asc())
        .all()
    )
    queries_by_day: dict[str, int] = defaultdict(int)
    bytes_by_day: dict[str, int] = defaultdict(int)
    success_count = 0
    fail_count = 0
    active_users: set[str] = set()
    total_bytes = 0
    for ev in events:
        day = _day_key(ev.created_at)
        queries_by_day[day] += 1
        bytes_by_day[day] += int(ev.bytes_billed or 0)
        total_bytes += int(ev.bytes_billed or 0)
        if ev.success:
            success_count += 1
            if ev.user_id:
                active_users.add(ev.user_id)
        else:
            fail_count += 1

    # Fill missing days for smoother charts
    day_list: list[str] = []
    cursor = since.date()
    end = now.date()
    while cursor <= end:
        day_list.append(cursor.isoformat())
        cursor += timedelta(days=1)

    recent_events = (
        db.query(QueryEvent).order_by(QueryEvent.created_at.desc()).limit(25).all()
    )

    return {
        "generated_at": now.isoformat(),
        "window_days": days,
        "mode": "mock" if settings.use_mock_data else "live",
        "private_access_mode": settings.private_access_mode,
        "users": {
            "total": len(users),
            "approved": by_status.get("APPROVED", 0),
            "waitlist_pending": by_status.get("WAITLIST_PENDING", 0),
            "suspended": by_status.get("SUSPENDED", 0),
            "verified": sum(1 for u in users if u.email_verified),
            "by_country": [
                {"country": k, "count": v}
                for k, v in sorted(by_country.items(), key=lambda x: (-x[1], x[0]))
                if k != "UN" or v > 0
            ][:20],
            "signups_by_day": [{"day": d, "count": signups_by_day.get(d, 0)} for d in day_list],
        },
        "queries": {
            "total": len(events),
            "success": success_count,
            "failed": fail_count,
            "active_users": len(active_users),
            "bytes_billed_total": total_bytes,
            "by_day": [
                {
                    "day": d,
                    "count": queries_by_day.get(d, 0),
                    "bytes_billed": bytes_by_day.get(d, 0),
                }
                for d in day_list
            ],
            "recent": [
                {
                    "id": e.id,
                    "user_id": e.user_id,
                    "success": e.success,
                    "mode": e.mode,
                    "bytes_billed": e.bytes_billed,
                    "row_count": e.row_count,
                    "error_code": e.error_code,
                    "sql_preview": e.sql_preview,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in recent_events
            ],
        },
        "policy": load_policy().to_public_dict(),
    }


@router.get("/health-check")
def admin_health(db: Session = Depends(get_db)) -> dict:
    users = db.query(func.count(User.id)).scalar() or 0
    events = db.query(func.count(QueryEvent.id)).scalar() or 0
    return {"ok": True, "users": users, "query_events": events}
