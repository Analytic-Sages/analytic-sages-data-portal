"""In-portal learning query endpoints + admin policy controls."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import require_key
from app.auth_users import require_admin, require_query_access
from app.bq_runner import QueryGuardError, friendly_query_error, run_learner_query
from app.db import get_db
from app.models import User
from app.query_events import log_query_event
from app.query_policy import load_policy, update_policy_from_dict

router = APIRouter(tags=["query"])


class RunQueryRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=20_000)


class AdminPolicyUpdate(BaseModel):
    enabled: bool | None = None
    max_bytes_billed: int | None = Field(default=None, ge=1_000_000, le=10_737_418_240)
    timeout_seconds: int | None = Field(default=None, ge=5, le=120)
    max_rows: int | None = Field(default=None, ge=1, le=1000)
    max_days: int | None = Field(default=None, ge=1, le=30)
    allowed_dataset: str | None = None
    allowed_tables: list[str] | None = None
    note: str | None = None


@router.get("/query/policy", dependencies=[Depends(require_key)])
def query_policy() -> dict:
    return load_policy().to_public_dict()


@router.post("/query/run", dependencies=[Depends(require_key)])
def query_run(
    body: RunQueryRequest,
    user: User = Depends(require_query_access),
    db: Session = Depends(get_db),
) -> dict:
    try:
        result = run_learner_query(body.sql)
        log_query_event(
            db,
            user_id=user.id,
            success=True,
            mode=str(result.get("mode") or "live"),
            bytes_billed=int(result.get("bytes_billed") or 0),
            bytes_processed=int(result.get("bytes_processed") or 0),
            row_count=int(result.get("row_count") or 0),
            sql=body.sql,
        )
        return result
    except QueryGuardError as exc:
        log_query_event(
            db,
            user_id=user.id,
            success=False,
            mode="error",
            error_code="QUERY_GUARD",
            sql=body.sql,
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface BQ errors cleanly to learners
        log_query_event(
            db,
            user_id=user.id,
            success=False,
            mode="error",
            error_code="BQ_FAILED",
            sql=body.sql,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=friendly_query_error(exc),
        ) from exc


@router.put("/admin/query-policy", dependencies=[Depends(require_admin)])
def admin_update_policy(body: AdminPolicyUpdate) -> dict:
    updates = body.model_dump(exclude_none=True)
    policy = update_policy_from_dict(updates)
    return {"status": "ok", "policy": policy.to_public_dict()}


@router.get("/admin/query-policy", dependencies=[Depends(require_admin)])
def admin_get_policy() -> dict:
    return load_policy().to_public_dict()
