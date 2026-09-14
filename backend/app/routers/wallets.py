"""Wallet activity endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_key
from app.cache import cache
from app.config import get_settings, table
from app.mock_data import MOCK_WALLET_ACTIVITY, filter_by_date
from app.trino_client import run_query
from app.validators import (
    validate_date_range,
    validate_limit,
    validate_offset,
    validate_solana_address,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _serialize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item = {}
        for key, value in row.items():
            if isinstance(value, date):
                item[key] = value.isoformat()
            else:
                item[key] = value
        out.append(item)
    return out


@router.get("/{address}/activity", dependencies=[Depends(require_key)])
def wallet_activity(
    address: str,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict:
    settings = get_settings()
    validate_solana_address(address, field="address")
    limit = validate_limit(limit)
    offset = validate_offset(offset)
    start_date, end_date = validate_date_range(start_date, end_date)

    cache_key = f"wallets:activity:{address}:{start_date}:{end_date}:{limit}:{offset}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if settings.use_mock_data:
        dated = filter_by_date(
            MOCK_WALLET_ACTIVITY, "block_date", start_date, end_date
        )
        matched = [r for r in dated if r["wallet"] == address]
        # Remap sample series so explore UI works for any valid address.
        rows = matched or [{**r, "wallet": address} for r in dated]
        rows = sorted(rows, key=lambda r: r["block_date"], reverse=True)
        payload = {
            "data": _serialize(rows[offset : offset + limit]),
            "limit": limit,
            "offset": offset,
            "mode": "mock",
        }
        cache.set(cache_key, payload, settings.cache_ttl_long)
        return payload

    clauses = ["wallet = ?"]
    params: list[Any] = [address]
    if start_date and end_date:
        clauses.append("block_date BETWEEN ? AND ?")
        params.extend([start_date.isoformat(), end_date.isoformat()])
    params.extend([limit, offset])

    sql = f"""
        SELECT block_date, wallet, transfer_count, total_volume,
               sent_volume, received_volume
        FROM {table("wallet_activity")}
        WHERE {" AND ".join(clauses)}
        ORDER BY block_date DESC
        LIMIT ? OFFSET ?
    """
    try:
        rows = run_query(sql, params)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    payload = {
        "data": _serialize(rows),
        "limit": limit,
        "offset": offset,
        "mode": "live",
    }
    cache.set(cache_key, payload, settings.cache_ttl_long)
    return payload
