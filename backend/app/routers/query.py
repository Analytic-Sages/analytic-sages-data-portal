"""In-portal learning query endpoints + admin policy controls."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import require_key
from app.auth_users import require_query_access
from app.bq_runner import QueryGuardError, run_learner_query
from app.models import User
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


def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    expected = os.environ.get("ADMIN_API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_KEY is not configured on the server",
        )
    if x_admin_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )


@router.get("/query/policy", dependencies=[Depends(require_key)])
def query_policy() -> dict:
    return load_policy().to_public_dict()


@router.post("/query/run", dependencies=[Depends(require_key)])
def query_run(
    body: RunQueryRequest,
    _user: User = Depends(require_query_access),
) -> dict:
    try:
        return run_learner_query(body.sql)
    except QueryGuardError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - surface BQ errors cleanly to learners
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"BigQuery query failed: {exc}",
        ) from exc


@router.put("/admin/query-policy", dependencies=[Depends(require_admin)])
def admin_update_policy(body: AdminPolicyUpdate) -> dict:
    updates = body.model_dump(exclude_none=True)
    policy = update_policy_from_dict(updates)
    return {"status": "ok", "policy": policy.to_public_dict()}


@router.get("/admin/query-policy", dependencies=[Depends(require_admin)])
def admin_get_policy() -> dict:
    return load_policy().to_public_dict()
