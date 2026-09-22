"""Recent curated transfer endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_key
from app.cache import cache
from app.config import get_settings, table
from app.mock_data import MOCK_TRANSFERS, filter_by_date
from app.trino_client import run_query
from app.validators import validate_date_range, validate_limit, validate_solana_address

router = APIRouter(prefix="/transfers", tags=["transfers"])


def _serialize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if isinstance(value, (date, datetime)):
                item[key] = value.isoformat()
            else:
                item[key] = value
        out.append(item)
    return out


@router.get("/recent", dependencies=[Depends(require_key)])
def transfers_recent(
    mint: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> dict:
    settings = get_settings()
    limit = validate_limit(limit)
    start_date, end_date = validate_date_range(start_date, end_date)
    if mint:
        validate_solana_address(mint, field="mint")

    cache_key = f"transfers:recent:{mint}:{start_date}:{end_date}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if settings.use_mock_data:
        rows = MOCK_TRANSFERS
        if mint:
            rows = [r for r in rows if r["mint"] == mint]
        if start_date and end_date:
            rows = filter_by_date(rows, "block_timestamp", start_date, end_date)
        rows = sorted(rows, key=lambda r: r["block_slot"], reverse=True)[:limit]
        payload = {"data": _serialize(rows), "limit": limit, "mode": "mock"}
        cache.set(cache_key, payload, settings.cache_ttl_short)
        return payload

    clauses = ["1=1"]
    params: list[Any] = []
    if mint:
        clauses.append("mint = ?")
        params.append(mint)
    if start_date and end_date:
        clauses.append("DATE(block_timestamp) BETWEEN ? AND ?")
        params.extend([start_date.isoformat(), end_date.isoformat()])
    params.append(limit)

    sql = f"""
        SELECT block_slot, block_timestamp, tx_signature, source, destination,
               mint, value, decimals, fee, memo, transfer_type
        FROM {table("transfers")}
        WHERE {" AND ".join(clauses)}
        ORDER BY block_slot DESC
        LIMIT ?
    """
    try:
        rows = run_query(sql, params)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    payload = {"data": _serialize(rows), "limit": limit, "mode": "live"}
    cache.set(cache_key, payload, settings.cache_ttl_short)
    return payload
