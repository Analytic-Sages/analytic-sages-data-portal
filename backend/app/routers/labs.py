"""Learning labs endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_key
from app.catalog import get_lab, list_labs

router = APIRouter(prefix="/labs", tags=["labs"])


@router.get("", dependencies=[Depends(require_key)])
def labs() -> dict:
    return {"labs": list_labs()}


@router.get("/{slug}", dependencies=[Depends(require_key)])
def lab_detail(slug: str) -> dict:
    lab = get_lab(slug)
    if lab is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lab not found: {slug}",
        )
    return lab
