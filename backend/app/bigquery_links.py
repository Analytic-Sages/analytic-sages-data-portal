"""BigQuery deep links and SQL helpers for the learner portal."""

from __future__ import annotations

import os
from urllib.parse import quote


def bq_project() -> str:
    return os.environ.get("BQ_PROJECT") or os.environ.get(
        "GCP_PROJECT", "analytic-sages-data-portal"
    )


def bq_dataset() -> str:
    return os.environ.get("BQ_CURATED_DATASET", "solana_curated")


def curated_table_id(table: str) -> str:
    """Learner-facing short id: dataset.table (project set in BigQuery UI)."""
    return f"{bq_dataset()}.{table}"


def curated_table_fqn(table: str) -> str:
    """Fully qualified project.dataset.table for ops / deep links."""
    return f"{bq_project()}.{bq_dataset()}.{table}"


def bigquery_table_url(table: str) -> str:
    project = bq_project()
    dataset = bq_dataset()
    return (
        f"https://console.cloud.google.com/bigquery"
        f"?project={quote(project)}"
        f"&ws=!1m5!1m4!4m3!1s{quote(project)}!2s{quote(dataset)}!3s{quote(table)}"
    )


def bigquery_console_url() -> str:
    return f"https://console.cloud.google.com/bigquery?project={quote(bq_project())}"
