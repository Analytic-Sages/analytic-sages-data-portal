"""Analytic Sages dashboard registry (Looker Studio embeds).

Portal owns catalog metadata. Looker Studio owns chart layout.
Learners never need the Looker Studio / Data Studio management API.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse

_EMBED_HOSTS = {
    "lookerstudio.google.com",
    "datastudio.google.com",
}

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

CATEGORIES = ("network", "token", "wallet", "protocol", "general")


LEARNING_NOTE_DEFAULT = (
    "Visualize curated Analytic Sages tables in Looker Studio. "
    "SQL labs teach querying; dashboards teach analysis."
)


@dataclass
class LookerDashboard:
    id: str
    slug: str
    title: str
    description: str
    category: str = "general"
    embed_url: str | None = None
    looker_report_url: str | None = None
    thumbnail_url: str | None = None
    is_published: bool = False
    sort_order: int = 100
    dataset_slugs: tuple[str, ...] = field(default_factory=tuple)
    charts_preview: tuple[str, ...] = field(default_factory=tuple)
    learning_note: str = LEARNING_NOTE_DEFAULT


    def to_public_dict(self) -> dict:
        ready = bool(self.is_published and self.embed_url)
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "embed_url": self.embed_url if ready else None,
            "looker_report_url": self.looker_report_url if ready else None,
            "thumbnail_url": self.thumbnail_url,
            "is_published": ready,
            "sort_order": self.sort_order,
            "dataset_slugs": list(self.dataset_slugs),
            "charts_preview": list(self.charts_preview),
            "learning_note": self.learning_note,
            "status": "live" if ready else "coming_soon",
        }

    def to_admin_dict(self) -> dict:
        data = asdict(self)
        data["dataset_slugs"] = list(self.dataset_slugs)
        data["charts_preview"] = list(self.charts_preview)
        data["status"] = (
            "live" if self.is_published and self.embed_url else "coming_soon"
        )
        return data


def dashboards_path() -> Path:
    return Path(
        os.environ.get(
            "LOOKER_DASHBOARDS_PATH",
            str(Path(__file__).resolve().parent.parent / "var" / "looker_dashboards.json"),
        )
    )


def default_catalog() -> list[LookerDashboard]:
    """Planned learning dashboards (visible even before embeds are wired)."""
    return [
        LookerDashboard(
            id="network-activity",
            slug="solana-network-activity",
            title="Solana Network Activity",
            description=(
                "Explore daily transactions, active wallets, and network volume "
                "on curated Analytic Sages Solana tables."
            ),
            category="network",
            sort_order=10,
            dataset_slugs=("transactions", "wallet_activity"),
            charts_preview=(
                "Daily transactions",
                "Active wallets",
                "Transaction volume",
                "Activity over time",
            ),
            is_published=False,
        ),
        LookerDashboard(
            id="token-intelligence",
            slug="solana-token-intelligence",
            title="Solana Token Intelligence",
            description=(
                "Transfer volume, top tokens, and sender/receiver patterns "
                "from curated token and transfer tables."
            ),
            category="token",
            sort_order=20,
            dataset_slugs=("transfers", "token_activity"),
            charts_preview=(
                "Transfer volume",
                "Transfer count",
                "Active tokens",
                "Unique senders and receivers",
            ),
            is_published=False,
        ),
        LookerDashboard(
            id="wallet-intelligence",
            slug="solana-wallet-intelligence",
            title="Solana Wallet Intelligence",
            description=(
                "Wallet activity, send/receive volume, and engagement patterns "
                "across curated wallet tables."
            ),
            category="wallet",
            sort_order=30,
            dataset_slugs=("wallet_activity", "transfers"),
            charts_preview=(
                "Active wallets",
                "Sent vs received volume",
                "Wallet activity over time",
            ),
            is_published=False,
        ),
        LookerDashboard(
            id="protocol-activity",
            slug="solana-protocol-activity",
            title="Solana Protocol Activity",
            description=(
                "Program and protocol activity for later phases. "
                "Placeholder until curated protocol datasets ship."
            ),
            category="protocol",
            sort_order=40,
            dataset_slugs=("transactions",),
            charts_preview=(
                "Program interactions",
                "Instruction counts",
                "User growth",
            ),
            is_published=False,
            learning_note="Coming in a later curriculum phase.",
        ),
    ]


def _normalize_embed_url(url: str | None) -> str | None:
    if url is None:
        return None
    raw = url.strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("embed_url must be https")
    host = (parsed.hostname or "").lower()
    if host not in _EMBED_HOSTS:
        raise ValueError(
            "embed_url must be a Looker Studio / Data Studio URL "
            "(lookerstudio.google.com or datastudio.google.com)"
        )
    if "/embed/" not in parsed.path and "/reporting/" in parsed.path:
        m = re.search(r"/reporting/([^/]+)", parsed.path)
        page = re.search(r"/page/([^/]+)", parsed.path)
        if m:
            base = f"https://lookerstudio.google.com/embed/reporting/{m.group(1)}"
            if page:
                return f"{base}/page/{page.group(1)}"
            return base
    if parsed.scheme == "http":
        return "https://" + raw[len("http://") :]
    return raw


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return s or "dashboard"


def _from_env() -> list[LookerDashboard] | None:
    """LOOKER_STUDIO_REPORTS=id|title|embed_url|dataset;... overrides defaults when set."""
    raw = os.environ.get("LOOKER_STUDIO_REPORTS", "").strip()
    if not raw:
        return None
    items: list[LookerDashboard] = []
    for idx, chunk in enumerate(raw.split(";")):
        parts = [p.strip() for p in chunk.split("|")]
        if len(parts) < 3:
            continue
        dash_id, title, embed = parts[0], parts[1], parts[2]
        dataset = parts[3] if len(parts) > 3 else None
        try:
            items.append(
                LookerDashboard(
                    id=dash_id,
                    slug=_slugify(dash_id),
                    title=title,
                    description="Learning dashboard",
                    category="general",
                    embed_url=_normalize_embed_url(embed),
                    is_published=True,
                    sort_order=(idx + 1) * 10,
                    dataset_slugs=(dataset,) if dataset else (),
                )
            )
        except ValueError:
            continue
    return items or None


def _parse_item(item: dict) -> LookerDashboard:
    title = str(item["title"]).strip()
    dash_id = str(item.get("id") or item.get("slug") or _slugify(title)).strip()
    slug = str(item.get("slug") or _slugify(dash_id)).strip()
    if not _SLUG_RE.match(slug):
        raise ValueError(f"Invalid dashboard slug: {slug}")
    category = str(item.get("category") or "general").strip().lower()
    if category not in CATEGORIES:
        category = "general"
    datasets = item.get("dataset_slugs") or item.get("dataset_slug")
    if isinstance(datasets, str):
        dataset_slugs = tuple(s.strip() for s in datasets.split(",") if s.strip())
    elif isinstance(datasets, list):
        dataset_slugs = tuple(str(s).strip() for s in datasets if str(s).strip())
    else:
        dataset_slugs = ()
    charts = item.get("charts_preview") or []
    if isinstance(charts, str):
        charts_preview = tuple(s.strip() for s in charts.split(",") if s.strip())
    else:
        charts_preview = tuple(str(s) for s in charts)
    embed = _normalize_embed_url(item.get("embed_url"))
    published = bool(item.get("is_published", bool(embed)))
    if published and not embed:
        raise ValueError(f"Dashboard `{slug}` is published but missing embed_url")
    return LookerDashboard(
        id=dash_id,
        slug=slug,
        title=title,
        description=str(item.get("description") or "").strip(),
        category=category,
        embed_url=embed,
        looker_report_url=(str(item["looker_report_url"]).strip() if item.get("looker_report_url") else None),
        thumbnail_url=(str(item["thumbnail_url"]).strip() if item.get("thumbnail_url") else None),
        is_published=published and bool(embed),
        sort_order=int(item.get("sort_order", 100)),
        dataset_slugs=dataset_slugs,
        charts_preview=charts_preview,
        learning_note=str(item.get("learning_note") or LEARNING_NOTE_DEFAULT),
    )


def _sort(items: list[LookerDashboard]) -> list[LookerDashboard]:
    return sorted(items, key=lambda d: (d.sort_order, d.title.lower()))


def load_dashboards(*, include_unpublished: bool = True) -> list[LookerDashboard]:
    path = dashboards_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text())
            items = raw.get("dashboards", raw if isinstance(raw, list) else [])
            out = _sort([_parse_item(item) for item in items])
            if include_unpublished:
                return out
            return [d for d in out if d.is_published and d.embed_url]
        except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
            pass

    env_items = _from_env()
    if env_items is not None:
        out = _sort(env_items)
        if include_unpublished:
            return out
        return [d for d in out if d.is_published and d.embed_url]

    out = _sort(default_catalog())
    if include_unpublished:
        return out
    return [d for d in out if d.is_published and d.embed_url]


def get_dashboard(slug: str) -> LookerDashboard | None:
    needle = slug.strip().lower()
    for item in load_dashboards(include_unpublished=True):
        if item.slug == needle or item.id == needle:
            return item
    return None


def save_dashboards(dashboards: list[LookerDashboard]) -> list[LookerDashboard]:
    path = dashboards_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dashboards": [
            {
                **asdict(d),
                "dataset_slugs": list(d.dataset_slugs),
                "charts_preview": list(d.charts_preview),
            }
            for d in _sort(dashboards)
        ]
    }
    path.write_text(json.dumps(payload, indent=2))
    return _sort(dashboards)


def replace_dashboards_from_dicts(items: list[dict]) -> list[LookerDashboard]:
    dashboards = [_parse_item(item) for item in items]
    slugs = [d.slug for d in dashboards]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Dashboard slugs must be unique")
    return save_dashboards(dashboards)


def dashboards_for_dataset(dataset_slug: str) -> list[LookerDashboard]:
    return [
        d
        for d in load_dashboards(include_unpublished=True)
        if dataset_slug in d.dataset_slugs
    ]


def learning_journey() -> dict:
    return {
        "steps": [
            {
                "id": "catalog",
                "title": "Understand",
                "path": "/catalog",
                "summary": "Browse curated datasets and schemas",
            },
            {
                "id": "labs",
                "title": "Learn",
                "path": "/labs",
                "summary": "Guided SQL labs",
            },
            {
                "id": "query",
                "title": "Query",
                "path": "/query",
                "summary": "Write SQL and visualize",
            },
            {
                "id": "dashboards",
                "title": "Build",
                "path": "/dashboards",
                "summary": "Save charts into dashboards",
            },
        ],
        "note": (
            "Dune-like loop inside Analytic Sages: SQL → results → ECharts → dashboard. "
            "Visualization is free in the browser; BigQuery stays under admin limits."
        ),
    }
