"""Guarded BigQuery runner for learning labs."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from app.bigquery_links import bq_project
from app.config import get_settings
from app.query_policy import QueryPolicy, load_policy

FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|CREATE|DROP|ALTER|TRUNCATE|EXPORT|LOAD|"
    r"GRANT|REVOKE|CALL|EXECUTE|SCRIPT)\b",
    re.IGNORECASE,
)
MULTI_STMT = re.compile(r";\s*\S", re.DOTALL)
DATE_LITERAL = re.compile(
    r"(?:DATE\s*)?'(\d{4}-\d{2}-\d{2})'|DATE\s+'(\d{4}-\d{2}-\d{2})'",
    re.IGNORECASE,
)
TABLE_REF = re.compile(
    r"(?:FROM|JOIN)\s+`?(?:([A-Za-z0-9_-]+)\.)?([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)`?",
    re.IGNORECASE,
)


class QueryGuardError(ValueError):
    pass


def validate_sql(sql: str, policy: QueryPolicy | None = None) -> str:
    policy = policy or load_policy()
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        raise QueryGuardError("SQL is empty")
    if len(cleaned) > 20_000:
        raise QueryGuardError("SQL is too long for the learning sandbox")
    if FORBIDDEN.search(cleaned):
        raise QueryGuardError(
            "Only read-only SELECT queries are allowed in the learning sandbox"
        )
    if MULTI_STMT.search(cleaned + " "):
        raise QueryGuardError("Multiple SQL statements are not allowed")
    if not re.match(r"^\s*(WITH|SELECT)\b", cleaned, re.IGNORECASE):
        raise QueryGuardError("Query must start with SELECT or WITH")

    refs = TABLE_REF.findall(cleaned)
    if not refs:
        raise QueryGuardError(
            f"Query must reference an allowed table like {policy.allowed_dataset}.token_transfers"
        )
    allowed = {f"{policy.allowed_dataset}.{t}" for t in policy.allowed_tables}
    for _project, dataset, table in refs:
        ref = f"{dataset}.{table}"
        if ref not in allowed:
            raise QueryGuardError(
                f"Table `{ref}` is not allowed. Allowed: {', '.join(sorted(allowed))}"
            )

    start, end = policy.window()
    for m in DATE_LITERAL.finditer(cleaned):
        raw = m.group(1) or m.group(2)
        try:
            d = date.fromisoformat(raw)
        except ValueError as exc:
            raise QueryGuardError(f"Invalid date literal: {raw}") from exc
        if d < start or d > end:
            raise QueryGuardError(
                f"Date {raw} is outside the learning window "
                f"({start.isoformat()} to {end.isoformat()}, max {policy.max_days} days)"
            )

    return cleaned


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    try:
        from decimal import Decimal

        if isinstance(value, Decimal):
            return float(value)
    except Exception:  # noqa: BLE001
        pass
    return value


def _rows_to_payload(result: Any, job: Any) -> tuple[list[str], list[dict[str, Any]]]:
    """Build columns + row dicts; prefer result.schema (job.schema is often empty)."""
    schema = getattr(result, "schema", None) or getattr(job, "schema", None)
    columns = [field.name for field in schema] if schema else []
    rows = list(result)
    if not columns and rows:
        first = rows[0]
        if hasattr(first, "keys"):
            columns = list(first.keys())
        else:
            columns = list(dict(first).keys())
    data = [{col: _serialize_value(row[col]) for col in columns} for row in rows]
    return columns, data


def run_learner_query(sql: str, policy: QueryPolicy | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    if not policy.enabled:
        raise QueryGuardError("In-portal querying is disabled by admin")

    cleaned = validate_sql(sql, policy)
    settings = get_settings()

    if settings.use_mock_data:
        from app.mock_query import mock_for_sql

        shaped = mock_for_sql(cleaned, policy)
        if shaped is not None:
            return shaped
        return _mock_result(cleaned, policy)

    try:
        from google.cloud import bigquery
    except ImportError as exc:
        raise QueryGuardError(
            "google-cloud-bigquery is not installed in the API environment"
        ) from exc

    client = bigquery.Client(project=bq_project())
    job_config = bigquery.QueryJobConfig(
        maximum_bytes_billed=policy.max_bytes_billed,
        use_query_cache=True,
        dry_run=False,
        job_timeout_ms=policy.timeout_seconds * 1000,
        labels={"as_portal": "learning", "sandbox": "true"},
    )

    # Dry-run first to estimate bytes and fail cheaply
    dry_config = bigquery.QueryJobConfig(
        dry_run=True,
        use_query_cache=False,
        maximum_bytes_billed=policy.max_bytes_billed,
    )
    dry_job = client.query(cleaned, job_config=dry_config)
    estimated = int(dry_job.total_bytes_processed or 0)
    if estimated > policy.max_bytes_billed:
        raise QueryGuardError(
            f"Query would scan ~{estimated} bytes, over the learning limit "
            f"of {policy.max_bytes_billed} bytes. Narrow the query or ask an admin "
            f"to raise QUERY_MAX_BYTES_BILLED."
        )

    limited_sql = (
        f"SELECT * FROM (\n{cleaned}\n) AS _as_learning_q\n"
        f"LIMIT {int(policy.max_rows)}"
    )
    job = client.query(limited_sql, job_config=job_config)
    result = job.result(timeout=policy.timeout_seconds)
    columns, data = _rows_to_payload(result, job)

    return {
        "columns": columns,
        "data": data,
        "row_count": len(data),
        "bytes_processed": int(job.total_bytes_processed or estimated),
        "bytes_billed": int(job.total_bytes_billed or 0),
        "job_id": job.job_id,
        "cache_hit": bool(job.cache_hit),
        "policy": policy.to_public_dict(),
        "mode": "live",
    }


def _mock_result(sql: str, policy: QueryPolicy) -> dict[str, Any]:
    start, end = policy.window()
    data = [
        {
            "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "sender": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
            "receiver": "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
            "amount": 1000.0 - i * 10,
            "block_timestamp": f"{end.isoformat()}T12:00:00+00:00",
        }
        for i in range(min(10, policy.max_rows))
    ]
    return {
        "columns": ["mint", "sender", "receiver", "amount", "block_timestamp"],
        "data": data,
        "row_count": len(data),
        "bytes_processed": 12345,
        "bytes_billed": 0,
        "job_id": "mock-learning-job",
        "cache_hit": True,
        "policy": policy.to_public_dict(),
        "mode": "mock",
        "sql": sql,
        "note": f"Mock learning result for window {start} to {end}",
    }
