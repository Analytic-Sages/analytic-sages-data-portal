"""Record learner query runs for admin analytics."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import QueryEvent


def log_query_event(
    db: Session,
    *,
    user_id: str | None,
    success: bool,
    mode: str = "",
    bytes_billed: int = 0,
    bytes_processed: int = 0,
    row_count: int = 0,
    error_code: str = "",
    sql: str = "",
) -> None:
    preview = " ".join(sql.split())[:240]
    db.add(
        QueryEvent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            success=success,
            mode=mode,
            bytes_billed=int(bytes_billed or 0),
            bytes_processed=int(bytes_processed or 0),
            row_count=int(row_count or 0),
            error_code=error_code[:64],
            sql_preview=preview,
        )
    )
    db.commit()
