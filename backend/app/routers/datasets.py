"""Curated dataset catalog for the learner portal."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_key
from app.catalog import get_dataset, list_datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", dependencies=[Depends(require_key)])
def datasets() -> dict:
    return {
        "product": "Analytic Sages Data Portal",
        "promise": "Learn Blockchain Through Data.",
        "description": (
            "Browse Analytic Sages curated Solana datasets, schemas, SQL examples, "
            "and learning labs. Run queries in the portal learning sandbox."
        ),
        "datasets": list_datasets(),
    }


@router.get("/{slug}", dependencies=[Depends(require_key)])
def dataset_detail(slug: str) -> dict:
    dataset = get_dataset(slug)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset not found: {slug}",
        )
    return dataset
