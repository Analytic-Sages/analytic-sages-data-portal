"""Dune-like studio API: visualizations + learner dashboards + public shares."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import require_key
from app.bq_runner import QueryGuardError, run_learner_query
from app import showcase, studio_store as store

router = APIRouter(tags=["studio"])


class ChartStyleIn(BaseModel):
    primary: str | None = None
    secondary: str | None = None
    background: str | None = None
    text: str | None = None
    muted: str | None = None
    palette: list[str] | None = None


class VisualizationIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    sql: str = Field(min_length=1, max_length=20_000)
    chart_type: str = Field(default="bar")
    x_axis: str | None = None
    y_axis: str | None = None
    description: str = ""
    style: ChartStyleIn | None = None


class DashboardIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    slug: str | None = None
    visualization_ids: list[str] = Field(default_factory=list)


class LayoutItemIn(BaseModel):
    i: str
    x: int = Field(ge=0, le=11)
    y: int = Field(ge=0, le=500)
    w: int = Field(ge=1, le=12)
    h: int = Field(ge=2, le=40)
    minW: int = 3
    minH: int = 4


class DashboardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    visualization_ids: list[str] | None = None
    layout: list[LayoutItemIn] | None = None
    theme: ChartStyleIn | None = None


class AddVizIn(BaseModel):
    visualization_id: str


class ShareIn(BaseModel):
    enabled: bool


class PublicRunIn(BaseModel):
    visualization_id: str


@router.get("/studio/visualizations", dependencies=[Depends(require_key)])
def list_visualizations() -> dict:
    items = store.list_visualizations()
    return {"visualizations": [v.to_dict() for v in items], "chart_types": list(store.CHART_TYPES), "default_style": store.DEFAULT_STYLE}


@router.post("/studio/visualizations", dependencies=[Depends(require_key)])
def create_visualization(body: VisualizationIn) -> dict:
    try:
        viz = store.create_visualization(
            title=body.title,
            sql=body.sql,
            chart_type=body.chart_type,
            x_axis=body.x_axis,
            y_axis=body.y_axis,
            description=body.description,
            style=body.style.model_dump(exclude_none=True) if body.style else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"visualization": viz.to_dict()}


@router.get("/studio/visualizations/{viz_id}", dependencies=[Depends(require_key)])
def get_visualization(viz_id: str) -> dict:
    viz = store.get_visualization(viz_id)
    if viz is None:
        raise HTTPException(status_code=404, detail="Visualization not found")
    return {"visualization": viz.to_dict()}


@router.delete("/studio/visualizations/{viz_id}", dependencies=[Depends(require_key)])
def delete_visualization(viz_id: str) -> dict:
    if not store.delete_visualization(viz_id):
        raise HTTPException(status_code=404, detail="Visualization not found")
    return {"status": "ok"}


@router.get("/studio/dashboards", dependencies=[Depends(require_key)])
def list_dashboards() -> dict:
    items = store.list_dashboards()
    return {
        "note": (
            "Native Analytic Sages dashboards with drag/resize layout and optional public share links. "
            "Charts render in-browser with ECharts."
        ),
        "dashboards": [d.to_dict() for d in items],
    }


@router.post("/studio/dashboards", dependencies=[Depends(require_key)])
def create_dashboard(body: DashboardIn) -> dict:
    try:
        board = store.create_dashboard(
            title=body.title,
            description=body.description,
            visualization_ids=body.visualization_ids,
            slug=body.slug,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"dashboard": board.to_dict()}


@router.get("/studio/dashboards/{slug}", dependencies=[Depends(require_key)])
def dashboard_detail(slug: str) -> dict:
    detail = store.dashboard_detail(slug)
    if detail is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return detail


@router.put("/studio/dashboards/{slug}", dependencies=[Depends(require_key)])
def update_dashboard(slug: str, body: DashboardUpdate) -> dict:
    try:
        board = store.update_dashboard(
            slug,
            title=body.title,
            description=body.description,
            visualization_ids=body.visualization_ids,
            layout=[item.model_dump() for item in body.layout] if body.layout is not None else None,
            theme=body.theme.model_dump(exclude_none=True) if body.theme is not None else None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dashboard not found") from exc
    return {"dashboard": board.to_dict()}


@router.post("/studio/dashboards/{slug}/visualizations", dependencies=[Depends(require_key)])
def add_visualization(slug: str, body: AddVizIn) -> dict:
    try:
        board = store.add_viz_to_dashboard(slug, body.visualization_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dashboard not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"dashboard": board.to_dict()}


@router.post("/studio/dashboards/{slug}/share", dependencies=[Depends(require_key)])
def share_dashboard(slug: str, body: ShareIn) -> dict:
    try:
        board = store.set_share(slug, enabled=body.enabled)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dashboard not found") from exc
    return {"dashboard": board.to_dict()}


@router.delete("/studio/dashboards/{slug}", dependencies=[Depends(require_key)])
def delete_dashboard(slug: str) -> dict:
    if not store.delete_dashboard(slug):
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return {"status": "ok"}


@router.get("/public/featured-dashboard")
def featured_dashboard() -> dict:
    detail = showcase.featured_detail()
    if detail is None:
        raise HTTPException(status_code=404, detail="Featured dashboard not available")
    return detail


@router.post("/public/featured-dashboard/run")
def featured_run(body: PublicRunIn) -> dict:
    try:
        return showcase.run_featured_viz(body.visualization_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Featured dashboard or visualization not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except QueryGuardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Query failed: {exc}") from exc


@router.get("/public/dashboards/{token}")
def public_dashboard(token: str) -> dict:
    detail = store.public_dashboard_detail(token)
    if detail is None:
        raise HTTPException(status_code=404, detail="Shared dashboard not found or sharing disabled")
    return detail


@router.post("/public/dashboards/{token}/run")
def public_run(token: str, body: PublicRunIn) -> dict:
    board = store.get_dashboard_by_share_token(token)
    if board is None:
        raise HTTPException(status_code=404, detail="Shared dashboard not found or sharing disabled")
    if body.visualization_id not in board.visualization_ids:
        raise HTTPException(status_code=400, detail="Visualization is not on this shared dashboard")
    viz = store.get_visualization(body.visualization_id)
    if viz is None:
        raise HTTPException(status_code=404, detail="Visualization not found")
    try:
        return run_learner_query(viz.sql)
    except QueryGuardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Query failed: {exc}") from exc
