"""Health and table contract endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import require_key
from app.config import get_settings, table
from app.trino_client import ping

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    if settings.use_mock_data:
        return {
            "status": "ok",
            "trino": "mock",
            "mode": "mock",
        }
    ok = ping()
    return {
        "status": "ok" if ok else "degraded",
        "trino": "up" if ok else "unreachable",
        "mode": "live",
    }


@router.get("/health/tables", dependencies=[Depends(require_key)])
def health_tables() -> dict:
    return {
        "token_activity": table("token_activity"),
        "wallet_activity": table("wallet_activity"),
        "transfers": table("transfers"),
        "tokens": table("tokens"),
    }
