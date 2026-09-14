# Backend API on Trino: implementation

Flow: FastAPI -> trino-python-client -> Trino (host port 8081) -> BigLake REST catalog -> GCS Iceberg.

## 1. What dbt-spark vs dbt_trino means in this repo

- `pyproject.toml` root + `Data-pipeline/run_dbt_v2.py`: legacy dbt-spark path for Dataproc Serverless. References `dbt_spark_v2/` which does not exist in the repo. Stale, do not use for the backend.
- `Data-pipeline/dbt_trino/`: current path. dbt-trino adapter, profile `trino` (catalog `biglake`, schema `gold`, host localhost:8080). Models:
  - `staging.stg_token_transfers`: view over `source('biglake_solana', 'token_transfers')` = `biglake.solana.token_transfers`
  - `gold.solana_token_daily`: incremental merge, key (day, mint)
  - `gold.solana_wallet_activity`: incremental merge, key (day, wallet)
- Backend `backend/` reads Trino directly with `trino` python package. It does not run dbt.

## 2. Table contract the API expects

Backend `app/config.py::table()` routes:

- `biglake.solana_marts.token_activity` for `/tokens/daily`, `/tokens/top`, `/tokens/{mint}`
- `biglake.solana_marts.wallet_activity` for `/wallets/{address}/activity`
- `biglake.solana.transfers` for `/transfers/recent`
- `biglake.solana.tokens` for token metadata

Expected columns (from routers):

- `token_activity(block_date, mint, transfer_count, total_volume, unique_senders, unique_receivers)`
- `wallet_activity(block_date, wallet, transfer_count, total_volume, sent_volume, received_volume)`
- `transfers(block_slot, block_timestamp, tx_signature, source, destination, mint, value, decimals, fee, memo, transfer_type)`

Known mismatch, fix before prod: `dbt_trino` gold models output `solana_token_daily(day, mint, total_volume, transfer_count)` and `solana_wallet_activity(day, wallet, total_volume, transfer_count)` in schema `gold`, with no `block_date`, no sender/receiver splits. Either rename gold models to `token_activity` / `wallet_activity` in schema `solana_marts` with the full column list, or create views aliasing them. Also `transfers` vs `token_transfers` naming differs; `build_iceberg_trino.py` defines the full transfer column set including fee/memo/transfer_type, so point the raw endpoint at whichever table actually exists.

## 3. Trino wiring

- Trino compose: `Data-pipeline/trino/docker-compose.yml`, image `trinodb/trino:483`, host port 8081 -> container 8080.
- Catalog: `Data-pipeline/trino/catalog/biglake.properties` (iceberg REST, uri `https://biglake.googleapis.com/iceberg/v1beta/restcatalog`, prefix `projects/analytic-sages-data-portal/catalogs/our-solana-lake-prod`, warehouse `gs://our-solana-lake-prod/warehouse`, header `x-goog-user-project`). Needs `BIGLAKE_TOKEN` env (user OAuth token, SA keys are blocked by org policy).
- `bronze.properties` is a local hive file metastore for raw parquet, not used by the API path.
- Backend compose: `backend/docker-compose.yml`, service `api`, env `TRINO_HOST` (default `host.docker.internal` in compose, `localhost` in code), `TRINO_PORT` 8081, `TRINO_CATALOG` biglake, `TRINO_SOURCE_SCHEMA` solana, `TRINO_MARTS_SCHEMA` solana_marts.

## 4. Backend layout

- `app/main.py`: FastAPI app, CORS GET only, routers health/datasets/tokens/wallets/transfers.
- `app/catalog.py`: learner-facing curated dataset metadata (schemas, SQL examples, labs, projects).
- `app/trino_client.py`: `run_query(sql, params)` opens one short-lived connection per query, returns list of dicts, wraps `TrinoQueryError` as RuntimeError. Always parameterized with `?` placeholders.
- `app/config.py`: env defaults, `MAX_LIMIT=100`, `DEFAULT_LIMIT=25`, `table()` router, `USE_MOCK_DATA`.
- `app/auth.py`: `require_key`, open when `API_KEY` empty, else checks `X-API-Key`.
- `app/validators.py`: base58 address check (32-44 chars), limit 1..100, date range max 90 days, start <= end.
- `app/cache.py`: in-memory TTL dict (`CACHE_TTL_SHORT=60`, `CACHE_TTL_LONG=600`). Same get/set interface a Redis swap can keep.
- `app/routers/tokens.py`, `wallets.py`, `transfers.py`, `health.py`, `datasets.py`: endpoint -> SQL / catalog mapping below.

## 5. Endpoint to SQL map

- `GET /health` -> `SELECT 1 AS ok`. Degraded if Trino unreachable.
- `GET /health/tables` -> returns fully qualified names from `config.table()`.
- `GET /tokens/daily?mint&start_date&end_date&limit&offset` -> select block_date, mint, transfer_count, total_volume, unique_senders, unique_receivers from token_activity, order block_date desc, limit/offset. Cache long TTL.
- `GET /tokens/top?start_date&end_date&limit` -> group by mint, sum volume, order desc.
- `GET /tokens/{mint}` -> metadata lookup on tokens source table.
- `GET /wallets/{address}/activity?start_date&end_date&limit&offset` -> select block_date, wallet, transfer_count, total_volume, sent_volume, received_volume from wallet_activity where wallet = ?. Cache long TTL.
- `GET /transfers/recent?mint&start_date&end_date&limit` -> raw rows from transfers source, order block_slot desc. Cache short TTL.

## 6. Run

Trino first (from `Data-pipeline/trino/`):

```
export BIGLAKE_TOKEN=$(gcloud auth print-access-token)
docker compose up -d
curl localhost:8081/v1/info
```

API (from `backend/`):

```
pip install -r requirements.txt
uvicorn app.main:app --port 8000
curl localhost:8000/health
curl localhost:8000/health/tables
curl "localhost:8000/tokens/daily?limit=5"
```

Docker:

```
docker compose up --build
```

Tests (offline, no Trino):

```
pytest tests/ -v
```

## 7. Verify Trino tables before starting API

```
trino --server localhost:8081 --catalog biglake --schema solana
SHOW TABLES FROM biglake.solana;
SHOW TABLES FROM biglake.solana_marts;
DESCRIBE biglake.solana_marts.token_activity;
SELECT * FROM biglake.solana_marts.token_activity LIMIT 5;
```

API is correct only if those DESCRIBE outputs match section 2. If they show `day` instead of `block_date`, fix the dbt models first.
