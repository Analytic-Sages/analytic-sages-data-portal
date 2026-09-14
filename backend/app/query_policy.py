"""Admin-controlled learning query policy.

This is for Analytic Sages learning labs only, not a Dune-style open query platform.
Limits are env defaults, overridable at runtime via admin API + policy file.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

def policy_path() -> Path:
    return Path(
        os.environ.get(
            "QUERY_POLICY_PATH",
            str(Path(__file__).resolve().parent.parent / "var" / "query_policy.json"),
        )
    )


@dataclass
class QueryPolicy:
    enabled: bool = True
    max_bytes_billed: int = 100 * 1024 * 1024  # 100 MiB
    timeout_seconds: int = 30
    max_rows: int = 100
    max_days: int = 2
    allowed_dataset: str = "solana_curated"
    allowed_tables: tuple[str, ...] = (
        "transfers",
        "transactions",
        "token_activity",
        "wallet_activity",
    )
    note: str = (
        "Learning sandbox only. Not a replacement for Dune or open blockchain analytics."
    )

    def window(self) -> tuple[date, date]:
        end = date.today()
        start = end - timedelta(days=max(self.max_days - 1, 0))
        return start, end

    def to_public_dict(self) -> dict:
        start, end = self.window()
        return {
            "enabled": self.enabled,
            "max_bytes_billed": self.max_bytes_billed,
            "max_bytes_billed_mb": round(self.max_bytes_billed / (1024 * 1024), 2),
            "timeout_seconds": self.timeout_seconds,
            "max_rows": self.max_rows,
            "max_days": self.max_days,
            "data_window_start": start.isoformat(),
            "data_window_end": end.isoformat(),
            "allowed_dataset": self.allowed_dataset,
            "allowed_tables": list(self.allowed_tables),
            "allowed_refs": [f"{self.allowed_dataset}.{t}" for t in self.allowed_tables],
            "note": self.note,
        }


def _from_env() -> QueryPolicy:
    tables = os.environ.get(
        "QUERY_ALLOWED_TABLES",
        "transfers,transactions,token_activity,wallet_activity",
    )
    return QueryPolicy(
        enabled=os.environ.get("QUERY_ENABLED", "1").lower() in {"1", "true", "yes"},
        max_bytes_billed=int(os.environ.get("QUERY_MAX_BYTES_BILLED", str(100 * 1024 * 1024))),
        timeout_seconds=int(os.environ.get("QUERY_TIMEOUT_SECONDS", "30")),
        max_rows=int(os.environ.get("QUERY_MAX_ROWS", "100")),
        max_days=int(os.environ.get("QUERY_MAX_DAYS", "2")),
        allowed_dataset=os.environ.get("QUERY_ALLOWED_DATASET")
        or os.environ.get("BQ_CURATED_DATASET", "solana_curated"),
        allowed_tables=tuple(t.strip() for t in tables.split(",") if t.strip()),
    )


def load_policy() -> QueryPolicy:
    base = _from_env()
    path = policy_path()
    if not path.exists():
        return base
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return base

    tables = raw.get("allowed_tables")
    return QueryPolicy(
        enabled=bool(raw.get("enabled", base.enabled)),
        max_bytes_billed=int(raw.get("max_bytes_billed", base.max_bytes_billed)),
        timeout_seconds=int(raw.get("timeout_seconds", base.timeout_seconds)),
        max_rows=int(raw.get("max_rows", base.max_rows)),
        max_days=int(raw.get("max_days", base.max_days)),
        allowed_dataset=str(raw.get("allowed_dataset", base.allowed_dataset)),
        allowed_tables=tuple(tables) if tables else base.allowed_tables,
        note=str(raw.get("note", base.note)),
    )


def save_policy(policy: QueryPolicy) -> QueryPolicy:
    path = policy_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(policy)
    payload["allowed_tables"] = list(policy.allowed_tables)
    path.write_text(json.dumps(payload, indent=2))
    return policy


def update_policy_from_dict(updates: dict) -> QueryPolicy:
    current = load_policy()
    data = asdict(current)
    data["allowed_tables"] = list(current.allowed_tables)
    for key, value in updates.items():
        if key in data and value is not None:
            data[key] = value
    if "allowed_tables" in data:
        data["allowed_tables"] = tuple(data["allowed_tables"])
    policy = QueryPolicy(**data)
    return save_policy(policy)
