"""Request validators for Solana addresses, limits, and date ranges."""

from __future__ import annotations

import re
from datetime import date, timedelta

from fastapi import HTTPException, status

from app.config import get_settings

BASE58_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
MAX_DATE_SPAN_DAYS = 90


def validate_solana_address(value: str, field: str = "address") -> str:
    if not BASE58_RE.fullmatch(value):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid Solana {field}: expected base58, 32-44 characters",
        )
    return value


def validate_limit(limit: int | None) -> int:
    settings = get_settings()
    if limit is None:
        return settings.default_limit
    if limit < 1 or limit > settings.max_limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"limit must be between 1 and {settings.max_limit}",
        )
    return limit


def validate_offset(offset: int | None) -> int:
    if offset is None:
        return 0
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="offset must be >= 0",
        )
    return offset


def validate_date_range(
    start_date: date | None,
    end_date: date | None,
) -> tuple[date | None, date | None]:
    if start_date is None and end_date is None:
        return None, None
    if start_date is None or end_date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date and end_date must be provided together",
        )
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="start_date must be <= end_date",
        )
    if (end_date - start_date) > timedelta(days=MAX_DATE_SPAN_DAYS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"date range cannot exceed {MAX_DATE_SPAN_DAYS} days",
        )
    return start_date, end_date
