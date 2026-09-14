"""Short-lived Trino connections with parameterized queries."""

from __future__ import annotations

from typing import Any

from app.config import get_settings


def run_query(sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
    """Execute SQL against Trino and return rows as dicts.

    Always use `?` placeholders with `params` for user-supplied values.
    """
    settings = get_settings()
    try:
        import trino.dbapi as trino_dbapi
        from trino.exceptions import TrinoQueryError
    except ImportError as exc:
        raise RuntimeError("trino package is not installed") from exc

    conn = trino_dbapi.connect(
        host=settings.trino_host,
        port=settings.trino_port,
        user=settings.trino_user,
        catalog=settings.trino_catalog,
        schema=settings.trino_source_schema,
        http_scheme="http",
    )
    try:
        cur = conn.cursor()
        try:
            cur.execute(sql, params or [])
            columns = [desc[0] for desc in (cur.description or [])]
            rows = cur.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except TrinoQueryError as exc:
            raise RuntimeError(f"Trino query failed: {exc}") from exc
        finally:
            cur.close()
    finally:
        conn.close()


def ping() -> bool:
    try:
        rows = run_query("SELECT 1 AS ok")
        return bool(rows and rows[0].get("ok") == 1)
    except Exception:
        return False
