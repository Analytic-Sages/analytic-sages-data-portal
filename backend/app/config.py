"""Environment-backed settings and table routing."""

from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    api_key: str
    trino_host: str
    trino_port: int
    trino_user: str
    trino_catalog: str
    trino_source_schema: str
    trino_marts_schema: str
    use_mock_data: bool
    cors_origins: list[str]
    max_limit: int = 100
    default_limit: int = 25
    cache_ttl_short: int = 60
    cache_ttl_long: int = 600
    curated_project: str = "analytic-sages-data-portal"
    curated_dataset: str = "solana_curated"

    def __init__(self) -> None:
        self.api_key = os.environ.get("API_KEY", "")
        self.trino_host = os.environ.get("TRINO_HOST", "localhost")
        self.trino_port = int(os.environ.get("TRINO_PORT", "8081"))
        self.trino_user = os.environ.get("TRINO_USER", "admin")
        self.trino_catalog = os.environ.get("TRINO_CATALOG", "biglake")
        self.trino_source_schema = os.environ.get("TRINO_SOURCE_SCHEMA", "solana")
        self.trino_marts_schema = os.environ.get("TRINO_MARTS_SCHEMA", "solana_marts")
        self.use_mock_data = os.environ.get("USE_MOCK_DATA", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        self.curated_project = os.environ.get(
            "BQ_PROJECT",
            os.environ.get("GCP_PROJECT", "analytic-sages-data-portal"),
        )
        self.curated_dataset = os.environ.get("BQ_CURATED_DATASET", "solana_curated")
        origins = os.environ.get(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        )
        self.cors_origins = [o.strip() for o in origins.split(",") if o.strip()]
        self.database_url = os.environ.get("DATABASE_URL", "")
        self.approved_tester_emails = os.environ.get("APPROVED_TESTER_EMAILS", "")
        self.frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
        self.cookie_secure = os.environ.get("COOKIE_SECURE", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        self.private_access_mode = os.environ.get("PRIVATE_ACCESS_MODE", "1").lower() in {
            "1",
            "true",
            "yes",
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


def table(name: str) -> str:
    """Return fully-qualified Trino table name for an internal table key."""
    s = get_settings()
    mapping = {
        "token_activity": f"{s.trino_catalog}.{s.trino_marts_schema}.token_activity",
        "wallet_activity": f"{s.trino_catalog}.{s.trino_marts_schema}.wallet_activity",
        "transfers": f"{s.trino_catalog}.{s.trino_source_schema}.transfers",
        "tokens": f"{s.trino_catalog}.{s.trino_source_schema}.tokens",
    }
    if name not in mapping:
        raise KeyError(f"Unknown table key: {name}")
    return mapping[name]


def curated_ref(slug: str) -> str:
    """Learner-facing BigQuery-style reference for a curated dataset."""
    s = get_settings()
    return f"{s.curated_project}.{s.curated_dataset}.{slug}"
