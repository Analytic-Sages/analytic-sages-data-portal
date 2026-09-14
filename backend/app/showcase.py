"""Featured homepage dashboard: hourly Solana activity showcase."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import studio_store as store

SHOWCASE_SLUG = "solana-hourly-showcase"
SHOWCASE_TITLE = "Solana Hourly Activity"
SHOWCASE_NOTE = (
    "Built from ~48 hours of curated Solana data. Each chart uses hourly SQL on "
    "transfer and transaction tables, the same workflow you will practice in Labs "
    "and Query Studio: filter by time, aggregate, visualize, and save to a dashboard."
)

_WINDOW = (
    "WHERE DATE(block_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)\n"
    "  AND CURRENT_DATE()"
)

# Stable IDs so re-seeding is idempotent.
VIZ_IDS = {
    "peak": "a1000001-0000-4000-8000-000000000001",
    "volume": "a1000002-0000-4000-8000-000000000002",
    "count": "a1000003-0000-4000-8000-000000000003",
    "tokens": "a1000004-0000-4000-8000-000000000004",
    "tx": "a1000005-0000-4000-8000-000000000005",
}

SHOWCASE_VIZ_DEFS: list[dict[str, Any]] = [
    {
        "id": VIZ_IDS["peak"],
        "title": "Peak hour transfer volume",
        "chart_type": "kpi",
        "x_axis": None,
        "y_axis": "peak_hour_volume",
        "sql": (
            "SELECT MAX(hourly_volume) AS peak_hour_volume\n"
            "FROM (\n"
            "  SELECT\n"
            "    TIMESTAMP_TRUNC(block_timestamp, HOUR) AS hour,\n"
            "    SUM(amount_ui) AS hourly_volume\n"
            "  FROM solana_curated.transfers\n"
            f"  {_WINDOW}\n"
            "  GROUP BY hour\n"
            ")"
        ),
    },
    {
        "id": VIZ_IDS["volume"],
        "title": "Transfer volume by hour",
        "chart_type": "line",
        "x_axis": "hour",
        "y_axis": "transfer_volume",
        "sql": (
            "SELECT\n"
            "  TIMESTAMP_TRUNC(block_timestamp, HOUR) AS hour,\n"
            "  SUM(amount_ui) AS transfer_volume\n"
            "FROM solana_curated.transfers\n"
            f"{_WINDOW}\n"
            "GROUP BY hour\n"
            "ORDER BY hour"
        ),
    },
    {
        "id": VIZ_IDS["count"],
        "title": "Transfer count by hour",
        "chart_type": "area",
        "x_axis": "hour",
        "y_axis": "transfer_count",
        "sql": (
            "SELECT\n"
            "  TIMESTAMP_TRUNC(block_timestamp, HOUR) AS hour,\n"
            "  COUNT(*) AS transfer_count\n"
            "FROM solana_curated.transfers\n"
            f"{_WINDOW}\n"
            "GROUP BY hour\n"
            "ORDER BY hour"
        ),
    },
    {
        "id": VIZ_IDS["tokens"],
        "title": "Top tokens by volume",
        "chart_type": "bar",
        "x_axis": "mint",
        "y_axis": "total_volume",
        "sql": (
            "SELECT\n"
            "  mint,\n"
            "  SUM(amount_ui) AS total_volume\n"
            "FROM solana_curated.transfers\n"
            f"{_WINDOW}\n"
            "GROUP BY mint\n"
            "ORDER BY total_volume DESC\n"
            "LIMIT 10"
        ),
    },
    {
        "id": VIZ_IDS["tx"],
        "title": "Transactions by hour",
        "chart_type": "line",
        "x_axis": "hour",
        "y_axis": "tx_count",
        "sql": (
            "SELECT\n"
            "  TIMESTAMP_TRUNC(block_timestamp, HOUR) AS hour,\n"
            "  COUNT(*) AS tx_count\n"
            "FROM solana_curated.transactions\n"
            f"{_WINDOW}\n"
            "GROUP BY hour\n"
            "ORDER BY hour"
        ),
    },
]

SHOWCASE_LAYOUT = [
    {"i": VIZ_IDS["peak"], "x": 0, "y": 0, "w": 3, "h": 6, "minW": 3, "minH": 5},
    {"i": VIZ_IDS["volume"], "x": 3, "y": 0, "w": 9, "h": 11, "minW": 4, "minH": 6},
    {"i": VIZ_IDS["count"], "x": 0, "y": 11, "w": 6, "h": 10, "minW": 4, "minH": 6},
    {"i": VIZ_IDS["tx"], "x": 6, "y": 11, "w": 6, "h": 10, "minW": 4, "minH": 6},
    {"i": VIZ_IDS["tokens"], "x": 0, "y": 21, "w": 12, "h": 12, "minW": 6, "minH": 6},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_showcase() -> store.StudioDashboard | None:
    """Create the featured showcase dashboard if it does not exist."""
    existing = store.get_dashboard(SHOWCASE_SLUG)
    if existing is not None:
        return existing

    data = store.load_store()
    now = _now()
    viz_ids: list[str] = []

    for spec in SHOWCASE_VIZ_DEFS:
        viz = store.Visualization(
            id=spec["id"],
            title=spec["title"],
            sql=spec["sql"],
            chart_type=spec["chart_type"],
            x_axis=spec.get("x_axis"),
            y_axis=spec["y_axis"],
            description="Analytic Sages homepage showcase",
            style=store.parse_style(None),
            created_at=now,
            updated_at=now,
        )
        data.visualizations.append(viz)
        viz_ids.append(viz.id)

    board = store.StudioDashboard(
        id="showcase-dashboard-0001",
        slug=SHOWCASE_SLUG,
        title=SHOWCASE_TITLE,
        description=SHOWCASE_NOTE,
        visualization_ids=viz_ids,
        layout=[store.LayoutItem(**item) for item in SHOWCASE_LAYOUT],
        theme=store.parse_style({"primary": "#F97316", "secondary": "#0B1F3A"}),
        is_published=True,
        share_enabled=True,
        share_token="as-hourly-showcase",
        created_at=now,
        updated_at=now,
    )
    data.dashboards.insert(0, board)
    store.save_store(data)
    return board


def featured_detail() -> dict | None:
    ensure_showcase()
    detail = store.dashboard_detail(SHOWCASE_SLUG)
    if detail is None:
        return None
    detail["read_only"] = True
    detail["featured"] = True
    return detail


def run_featured_viz(viz_id: str) -> dict:
    from app.bq_runner import QueryGuardError, run_learner_query

    ensure_showcase()
    board = store.get_dashboard(SHOWCASE_SLUG)
    if board is None:
        raise KeyError(SHOWCASE_SLUG)
    if viz_id not in board.visualization_ids:
        raise ValueError("Visualization is not on the featured dashboard")
    viz = store.get_visualization(viz_id)
    if viz is None:
        raise KeyError(viz_id)
    return run_learner_query(viz.sql)
