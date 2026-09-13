"""Shared Trino client for Solana lakehouse. No Spark dependency."""
import os
import sys

# Local ./trino/ config dir shadows the PyPI `trino` package when the
# project root is on sys.path. Drop those entries before importing.
for _p in list(sys.path):
    _base = os.path.abspath(_p) if _p else os.getcwd()
    if os.path.isdir(os.path.join(_base, "trino", "catalog")):
        sys.path.remove(_p)

try:
    import trino.dbapi as trino_dbapi
    HAS_TRINO = True
except ImportError:
    HAS_TRINO = False


def get_conn(catalog=None, schema=None):
    if not HAS_TRINO:
        raise ImportError("pip install trino")
    return trino_dbapi.connect(
        host=os.environ.get("TRINO_HOST", "localhost"),
        port=int(os.environ.get("TRINO_PORT", "8080")),
        user=os.environ.get("TRINO_USER", "admin"),
        catalog=catalog or os.environ.get("TRINO_CATALOG", "biglake"),
        schema=schema or os.environ.get("TRINO_SCHEMA", "solana"),
        http_scheme=os.environ.get("TRINO_SCHEME", "http"),
    )


def run(sql, catalog=None, schema=None):
    conn = get_conn(catalog, schema)
    cur = conn.cursor()
    cur.execute(sql)
    try:
        rows = cur.fetchall()
    except Exception:
        rows = []
    return rows
