"""Local learner studio: saved visualizations + dashboards (Dune-like, $0 charts).

Persisted as JSON. Charts render in the browser via ECharts; this store only keeps
SQL + chart config + board layout. Queries still go through the guarded BigQuery runner.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CHART_TYPES = ("line", "bar", "area", "pie", "scatter", "kpi")
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
GRID_COLS = 12
DEFAULT_W = 6
DEFAULT_H = 8

DEFAULT_STYLE: dict[str, Any] = {
    "primary": "#F97316",
    "secondary": "#0B1F3A",
    "background": "#FFFFFF",
    "text": "#0B1F3A",
    "muted": "#64748B",
    "palette": ["#F97316", "#0B1F3A", "#38BDF8", "#A78BFA", "#34D399", "#FBBF24"],
}


def _normalize_hex(value: str, fallback: str) -> str:
    raw = (value or "").strip()
    if not _HEX_RE.match(raw):
        return fallback
    if len(raw) == 4:
        return "#" + "".join(ch * 2 for ch in raw[1:]).upper()
    return "#" + raw[1:].upper()


def parse_style(raw: Any | None) -> dict[str, Any]:
    base: dict[str, Any] = {
        "primary": DEFAULT_STYLE["primary"],
        "secondary": DEFAULT_STYLE["secondary"],
        "background": DEFAULT_STYLE["background"],
        "text": DEFAULT_STYLE["text"],
        "muted": DEFAULT_STYLE["muted"],
        "palette": list(DEFAULT_STYLE["palette"]),
    }
    if not isinstance(raw, dict):
        return base
    for key in ("primary", "secondary", "background", "text", "muted"):
        if raw.get(key):
            base[key] = _normalize_hex(str(raw[key]), base[key])
    palette = raw.get("palette")
    if isinstance(palette, list) and palette:
        cleaned = [_normalize_hex(str(c), DEFAULT_STYLE["primary"]) for c in palette[:12]]
        if cleaned:
            base["palette"] = cleaned
    return base


def studio_path() -> Path:
    return Path(
        os.environ.get(
            "STUDIO_STORE_PATH",
            str(Path(__file__).resolve().parent.parent / "var" / "studio_store.json"),
        )
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Visualization:
    id: str
    title: str
    sql: str
    chart_type: str
    x_axis: str | None
    y_axis: str | None
    description: str = ""
    style: dict[str, Any] = field(default_factory=lambda: parse_style(None))
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        data = asdict(self)
        data["style"] = parse_style(self.style)
        return data


@dataclass
class LayoutItem:
    i: str
    x: int
    y: int
    w: int
    h: int
    minW: int = 3
    minH: int = 4

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StudioDashboard:
    id: str
    slug: str
    title: str
    description: str = ""
    visualization_ids: list[str] = field(default_factory=list)
    layout: list[LayoutItem] = field(default_factory=list)
    theme: dict[str, Any] = field(default_factory=lambda: parse_style(None))
    is_published: bool = True
    share_enabled: bool = False
    share_token: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "visualization_ids": list(self.visualization_ids),
            "layout": [item.to_dict() for item in self.layout],
            "theme": parse_style(self.theme),
            "is_published": self.is_published,
            "share_enabled": self.share_enabled,
            "share_token": self.share_token if self.share_enabled else None,
            "share_path": (
                f"/share/{self.share_token}" if self.share_enabled and self.share_token else None
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_public_dict(self) -> dict:
        data = self.to_dict()
        # Public viewers don't need the raw token management fields beyond path
        data.pop("share_token", None)
        return data


@dataclass
class StudioStore:
    visualizations: list[Visualization] = field(default_factory=list)
    dashboards: list[StudioDashboard] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "visualizations": [v.to_dict() for v in self.visualizations],
            "dashboards": [d.to_dict() for d in self.dashboards],
        }


def _empty() -> StudioStore:
    return StudioStore()


def _parse_layout(raw: Any) -> list[LayoutItem]:
    items: list[LayoutItem] = []
    if not isinstance(raw, list):
        return items
    for item in raw:
        try:
            items.append(
                LayoutItem(
                    i=str(item["i"]),
                    x=int(item.get("x", 0)),
                    y=int(item.get("y", 0)),
                    w=int(item.get("w", DEFAULT_W)),
                    h=int(item.get("h", DEFAULT_H)),
                    minW=int(item.get("minW", 3)),
                    minH=int(item.get("minH", 4)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return items


def _default_layout_for(viz_ids: list[str], existing: list[LayoutItem] | None = None) -> list[LayoutItem]:
    by_id = {item.i: item for item in (existing or [])}
    layout: list[LayoutItem] = []
    cursor_y = 0
    for idx, viz_id in enumerate(viz_ids):
        if viz_id in by_id:
            layout.append(by_id[viz_id])
            cursor_y = max(cursor_y, by_id[viz_id].y + by_id[viz_id].h)
            continue
        x = 0 if idx % 2 == 0 else DEFAULT_W
        if idx % 2 == 0 and idx > 0:
            cursor_y += DEFAULT_H
        y = cursor_y if idx % 2 == 0 else cursor_y
        if idx % 2 == 1:
            # place on same row as previous
            prev = layout[-1] if layout else None
            y = prev.y if prev else cursor_y
        layout.append(
            LayoutItem(i=viz_id, x=x, y=y, w=DEFAULT_W, h=DEFAULT_H)
        )
    return layout


def load_store() -> StudioStore:
    path = studio_path()
    if not path.exists():
        return _empty()
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return _empty()

    viz: list[Visualization] = []
    for item in raw.get("visualizations", []):
        viz.append(
            Visualization(
                id=str(item["id"]),
                title=str(item["title"]),
                sql=str(item["sql"]),
                chart_type=str(item.get("chart_type") or "bar"),
                x_axis=item.get("x_axis"),
                y_axis=item.get("y_axis"),
                description=str(item.get("description") or ""),
                style=parse_style(item.get("style")),
                created_at=str(item.get("created_at") or ""),
                updated_at=str(item.get("updated_at") or ""),
            )
        )
    boards: list[StudioDashboard] = []
    for item in raw.get("dashboards", []):
        viz_ids = [str(x) for x in item.get("visualization_ids", [])]
        layout = _parse_layout(item.get("layout"))
        if not layout and viz_ids:
            layout = _default_layout_for(viz_ids)
        boards.append(
            StudioDashboard(
                id=str(item["id"]),
                slug=str(item["slug"]),
                title=str(item["title"]),
                description=str(item.get("description") or ""),
                visualization_ids=viz_ids,
                layout=layout,
                theme=parse_style(item.get("theme")),
                is_published=bool(item.get("is_published", True)),
                share_enabled=bool(item.get("share_enabled", False)),
                share_token=(str(item["share_token"]) if item.get("share_token") else None),
                created_at=str(item.get("created_at") or ""),
                updated_at=str(item.get("updated_at") or ""),
            )
        )
    return StudioStore(visualizations=viz, dashboards=boards)


def save_store(store: StudioStore) -> StudioStore:
    path = studio_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Persist share_token even when disabled so re-enable can reuse; store raw boards
    payload = {
        "visualizations": [v.to_dict() for v in store.visualizations],
        "dashboards": [
            {
                "id": d.id,
                "slug": d.slug,
                "title": d.title,
                "description": d.description,
                "visualization_ids": list(d.visualization_ids),
                "layout": [item.to_dict() for item in d.layout],
                "theme": parse_style(d.theme),
                "is_published": d.is_published,
                "share_enabled": d.share_enabled,
                "share_token": d.share_token,
                "created_at": d.created_at,
                "updated_at": d.updated_at,
            }
            for d in store.dashboards
        ],
    }
    path.write_text(json.dumps(payload, indent=2))
    return store


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s or f"dashboard-{uuid.uuid4().hex[:8]}"


def create_visualization(
    *,
    title: str,
    sql: str,
    chart_type: str,
    x_axis: str | None,
    y_axis: str | None,
    description: str = "",
    style: dict | None = None,
) -> Visualization:
    if chart_type not in CHART_TYPES:
        raise ValueError(f"chart_type must be one of {CHART_TYPES}")
    if not title.strip():
        raise ValueError("title is required")
    if not sql.strip():
        raise ValueError("sql is required")
    if chart_type != "kpi" and not x_axis:
        raise ValueError("x_axis is required for this chart type")
    if chart_type in {"line", "bar", "area", "scatter", "kpi", "pie"} and not y_axis:
        raise ValueError("y_axis is required")

    store = load_store()
    now = _now()
    viz = Visualization(
        id=str(uuid.uuid4()),
        title=title.strip(),
        sql=sql.strip(),
        chart_type=chart_type,
        x_axis=x_axis,
        y_axis=y_axis,
        description=description.strip(),
        style=parse_style(style),
        created_at=now,
        updated_at=now,
    )
    store.visualizations.insert(0, viz)
    save_store(store)
    return viz


def list_visualizations() -> list[Visualization]:
    return load_store().visualizations


def get_visualization(viz_id: str) -> Visualization | None:
    for item in load_store().visualizations:
        if item.id == viz_id:
            return item
    return None


def delete_visualization(viz_id: str) -> bool:
    store = load_store()
    before = len(store.visualizations)
    store.visualizations = [v for v in store.visualizations if v.id != viz_id]
    for board in store.dashboards:
        board.visualization_ids = [x for x in board.visualization_ids if x != viz_id]
        board.layout = [item for item in board.layout if item.i != viz_id]
        board.updated_at = _now()
    if len(store.visualizations) == before:
        return False
    save_store(store)
    return True


def create_dashboard(
    *,
    title: str,
    description: str = "",
    visualization_ids: list[str] | None = None,
    slug: str | None = None,
) -> StudioDashboard:
    if not title.strip():
        raise ValueError("title is required")
    store = load_store()
    base = _slugify(slug or title)
    slug_final = base
    existing = {d.slug for d in store.dashboards}
    n = 2
    while slug_final in existing:
        slug_final = f"{base}-{n}"
        n += 1
    if not _SLUG_RE.match(slug_final):
        raise ValueError(f"Invalid slug: {slug_final}")

    known = {v.id for v in store.visualizations}
    ids = [x for x in (visualization_ids or []) if x in known]
    now = _now()
    board = StudioDashboard(
        id=str(uuid.uuid4()),
        slug=slug_final,
        title=title.strip(),
        description=description.strip(),
        visualization_ids=ids,
        layout=_default_layout_for(ids),
        theme=parse_style(None),
        is_published=True,
        share_enabled=False,
        share_token=None,
        created_at=now,
        updated_at=now,
    )
    store.dashboards.insert(0, board)
    save_store(store)
    return board


def list_dashboards() -> list[StudioDashboard]:
    return load_store().dashboards


def get_dashboard(slug: str) -> StudioDashboard | None:
    needle = slug.strip().lower()
    for item in load_store().dashboards:
        if item.slug == needle or item.id == needle:
            return item
    return None


def get_dashboard_by_share_token(token: str) -> StudioDashboard | None:
    needle = token.strip()
    if not needle:
        return None
    for item in load_store().dashboards:
        if item.share_enabled and item.share_token == needle:
            return item
    return None


def update_dashboard(
    slug: str,
    *,
    title: str | None = None,
    description: str | None = None,
    visualization_ids: list[str] | None = None,
    layout: list[dict] | None = None,
    theme: dict | None = None,
) -> StudioDashboard:
    store = load_store()
    board = None
    for item in store.dashboards:
        if item.slug == slug or item.id == slug:
            board = item
            break
    if board is None:
        raise KeyError(slug)
    if title is not None:
        board.title = title.strip() or board.title
    if description is not None:
        board.description = description.strip()
    if visualization_ids is not None:
        known = {v.id for v in store.visualizations}
        board.visualization_ids = [x for x in visualization_ids if x in known]
        board.layout = _default_layout_for(board.visualization_ids, board.layout)
    if layout is not None:
        parsed = _parse_layout(layout)
        allowed = set(board.visualization_ids)
        board.layout = [item for item in parsed if item.i in allowed]
    if theme is not None:
        board.theme = parse_style(theme)
    board.updated_at = _now()
    save_store(store)
    return board


def add_viz_to_dashboard(slug: str, viz_id: str) -> StudioDashboard:
    store = load_store()
    if not any(v.id == viz_id for v in store.visualizations):
        raise ValueError("Visualization not found")
    board = None
    for item in store.dashboards:
        if item.slug == slug or item.id == slug:
            board = item
            break
    if board is None:
        raise KeyError(slug)
    if viz_id not in board.visualization_ids:
        board.visualization_ids.append(viz_id)
        board.layout = _default_layout_for(board.visualization_ids, board.layout)
    board.updated_at = _now()
    save_store(store)
    return board


def set_share(slug: str, *, enabled: bool) -> StudioDashboard:
    store = load_store()
    board = None
    for item in store.dashboards:
        if item.slug == slug or item.id == slug:
            board = item
            break
    if board is None:
        raise KeyError(slug)
    board.share_enabled = enabled
    if enabled:
        if not board.share_token:
            board.share_token = secrets.token_urlsafe(18)
    board.updated_at = _now()
    save_store(store)
    return board


def delete_dashboard(slug: str) -> bool:
    store = load_store()
    before = len(store.dashboards)
    store.dashboards = [d for d in store.dashboards if d.slug != slug and d.id != slug]
    if len(store.dashboards) == before:
        return False
    save_store(store)
    return True


def dashboard_detail(slug: str) -> dict | None:
    board = get_dashboard(slug)
    if board is None:
        return None
    store = load_store()
    by_id = {v.id: v for v in store.visualizations}
    charts = [by_id[i].to_dict() for i in board.visualization_ids if i in by_id]
    # Keep layout in sync with viz ids
    if len(board.layout) != len(board.visualization_ids) or {
        item.i for item in board.layout
    } != set(board.visualization_ids):
        board.layout = _default_layout_for(board.visualization_ids, board.layout)
        save_store(store)
    return {"dashboard": board.to_dict(), "visualizations": charts}


def public_dashboard_detail(token: str) -> dict | None:
    board = get_dashboard_by_share_token(token)
    if board is None:
        return None
    store = load_store()
    by_id = {v.id: v for v in store.visualizations}
    charts = [by_id[i].to_dict() for i in board.visualization_ids if i in by_id]
    return {
        "dashboard": board.to_public_dict(),
        "visualizations": charts,
        "read_only": True,
    }
