"""Looker Studio dashboard registry for the learning portal."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import require_key
from app.auth_users import require_admin
from app.dashboards import (
    get_dashboard,
    learning_journey,
    load_dashboards,
    replace_dashboards_from_dicts,
)

router = APIRouter(tags=["dashboards"])


class DashboardIn(BaseModel):
    id: str | None = Field(default=None, max_length=64)
    slug: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    category: str = "general"
    embed_url: str | None = Field(default=None, max_length=2000)
    looker_report_url: str | None = Field(default=None, max_length=2000)
    thumbnail_url: str | None = Field(default=None, max_length=2000)
    is_published: bool = False
    sort_order: int = Field(default=100, ge=0, le=10_000)
    dataset_slugs: list[str] = Field(default_factory=list)
    charts_preview: list[str] = Field(default_factory=list)
    learning_note: str | None = None


class DashboardsReplace(BaseModel):
    dashboards: list[DashboardIn] = Field(default_factory=list)


@router.get("/learning-journey", dependencies=[Depends(require_key)])
def get_learning_journey() -> dict:
    return learning_journey()


@router.get("/dashboards", dependencies=[Depends(require_key)])
def list_dashboards(dataset: str | None = None) -> dict:
    items = load_dashboards(include_unpublished=True)
    if dataset:
        items = [d for d in items if dataset in d.dataset_slugs]
    live = [d for d in items if d.is_published and d.embed_url]
    return {
        "product": "Analytic Sages Data Portal",
        "note": (
            "Dashboards visualize curated Analytic Sages tables in Looker Studio. "
            "SQL labs teach querying; dashboards teach analysis. "
            "Portal query result rows are not piped into Looker Studio."
        ),
        "journey": learning_journey(),
        "counts": {
            "total": len(items),
            "live": len(live),
            "coming_soon": len(items) - len(live),
        },
        "dashboards": [d.to_public_dict() for d in items],
    }


@router.get("/dashboards/{slug}", dependencies=[Depends(require_key)])
def dashboard_detail(slug: str) -> dict:
    item = get_dashboard(slug)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard not found: {slug}",
        )
    related = [
        d.to_public_dict()
        for d in load_dashboards(include_unpublished=True)
        if d.slug != item.slug and set(d.dataset_slugs) & set(item.dataset_slugs)
    ][:4]
    return {
        "dashboard": item.to_public_dict(),
        "related": related,
        "journey": learning_journey(),
    }


@router.get("/admin/dashboards", dependencies=[Depends(require_admin)])
def admin_list_dashboards() -> dict:
    return {
        "dashboards": [d.to_admin_dict() for d in load_dashboards(include_unpublished=True)]
    }


@router.put("/admin/dashboards", dependencies=[Depends(require_admin)])
def admin_replace_dashboards(body: DashboardsReplace) -> dict:
    try:
        saved = replace_dashboards_from_dicts([d.model_dump(exclude_none=True) for d in body.dashboards])
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "status": "ok",
        "dashboards": [d.to_admin_dict() for d in saved],
    }
