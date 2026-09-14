"""Token activity and metadata endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_key
from app.cache import cache
from app.config import get_settings, table
from app.mock_data import MOCK_TOKEN_ACTIVITY, MOCK_TOKENS, filter_by_date
from app.trino_client import run_query
from app.validators import (
    validate_date_range,
    validate_limit,
    validate_offset,
    validate_solana_address,
)

router = APIRouter(prefix="/tokens", tags=["tokens"])


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


@router.get("/daily", dependencies=[Depends(require_key)])
def tokens_daily(
    mint: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict:
    settings = get_settings()
    limit = validate_limit(limit)
    offset = validate_offset(offset)
    start_date, end_date = validate_date_range(start_date, end_date)
    if mint:
        validate_solana_address(mint, field="mint")

    cache_key = f"tokens:daily:{mint}:{start_date}:{end_date}:{limit}:{offset}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if settings.use_mock_data:
        rows = filter_by_date(MOCK_TOKEN_ACTIVITY, "block_date", start_date, end_date)
        if mint:
            rows = [r for r in rows if r["mint"] == mint]
        rows = sorted(rows, key=lambda r: r["block_date"], reverse=True)
        payload = {
            "data": _serialize(rows[offset : offset + limit]),
            "limit": limit,
            "offset": offset,
            "mode": "mock",
        }
        cache.set(cache_key, payload, settings.cache_ttl_long)
        return payload

    clauses = ["1=1"]
    params: list[Any] = []
    if mint:
        clauses.append("mint = ?")
        params.append(mint)
    if start_date and end_date:
        clauses.append("block_date BETWEEN ? AND ?")
        params.extend([start_date.isoformat(), end_date.isoformat()])
    params.extend([limit, offset])

    sql = f"""
        SELECT block_date, mint, transfer_count, total_volume,
               unique_senders, unique_receivers
        FROM {table("token_activity")}
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


@router.get("/top", dependencies=[Depends(require_key)])
def tokens_top(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> dict:
    settings = get_settings()
    limit = validate_limit(limit)
    start_date, end_date = validate_date_range(start_date, end_date)

    cache_key = f"tokens:top:{start_date}:{end_date}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if settings.use_mock_data:
        rows = filter_by_date(MOCK_TOKEN_ACTIVITY, "block_date", start_date, end_date)
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        for row in rows:
            mint = row["mint"]
            totals[mint] = totals.get(mint, 0.0) + float(row["total_volume"])
            counts[mint] = counts.get(mint, 0) + int(row["transfer_count"])
        ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        payload = {
            "data": [
                {
                    "mint": mint,
                    "total_volume": volume,
                    "transfer_count": counts[mint],
                }
                for mint, volume in ranked
            ],
            "limit": limit,
            "mode": "mock",
        }
        cache.set(cache_key, payload, settings.cache_ttl_long)
        return payload

    clauses = ["1=1"]
    params: list[Any] = []
    if start_date and end_date:
        clauses.append("block_date BETWEEN ? AND ?")
        params.extend([start_date.isoformat(), end_date.isoformat()])
    params.append(limit)

    sql = f"""
        SELECT mint,
               SUM(total_volume) AS total_volume,
               SUM(transfer_count) AS transfer_count
        FROM {table("token_activity")}
        WHERE {" AND ".join(clauses)}
        GROUP BY mint
        ORDER BY total_volume DESC
        LIMIT ?
    """
    try:
        rows = run_query(sql, params)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    payload = {"data": rows, "limit": limit, "mode": "live"}
    cache.set(cache_key, payload, settings.cache_ttl_long)
    return payload


@router.get("/{mint}", dependencies=[Depends(require_key)])
def token_metadata(mint: str) -> dict:
    settings = get_settings()
    validate_solana_address(mint, field="mint")

    if settings.use_mock_data:
        for token in MOCK_TOKENS:
            if token["mint"] == mint:
                return {"data": token, "mode": "mock"}
        raise HTTPException(status_code=404, detail="Token not found")

    sql = f"""
        SELECT mint, name, symbol, decimals, is_nft
        FROM {table("tokens")}
        WHERE mint = ?
        LIMIT 1
    """
    try:
        rows = run_query(sql, [mint])
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    if not rows:
        raise HTTPException(status_code=404, detail="Token not found")
    return {"data": rows[0], "mode": "live"}
