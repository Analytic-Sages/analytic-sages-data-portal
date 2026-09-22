# Implementation: Postgres → GCS Parquet Exporter (Production)

## Goal
Envio HyperIndex (`Data-pipeline/indexer/`) indexes **all** SPL Token + Token-2022 `transfer` instructions into local Postgres (`envio-postgres:5433`, `Transfer` per-row) as **transient hot buffer**. Exporter script `Data-pipeline/jobs/ingestion/export_transfers_to_gcs.py` moves rows to GCS Parquet lakehouse `gs://our-solana-lake-prod/indexer/transfers/` for long-term truth, queried via Trino Iceberg `lake.solana.transfers`. Postgres retains ~24h then prunes.

No Cloud SQL required; GCS is lake, Postgres is queue.

## Architecture (Prod)

```
En v ion indexer (config.yaml: start_slot slot, programs SplToken+Token2022, fields path/accountActivity)
   ↓ context.Transfer.set (id=slot-txIndex-path, mint/sender/receiver/amount/decimals/normalizedAmount)
envio-postgres:5433 (Docker, PD-mounted volume, schema ENVIO_PG_SCHEMA=solana_transfer_raw)
   ↓
Exporter (jobs/ingestion/export_transfers_to_gcs.py, systemd timer / Airflow, every 15m or hourly)
   → SELECT ... WHERE id > watermark ORDER BY id LIMIT 50k (streaming cursor)
   → pyarrow Parquet, partitioned dt=YYYY-MM-DD daily (ZSTD) for Spark Iceberg
   → GCS temp prefix gs://.../indexer/transfers/_tmp/uuid/ → atomic compose/rename to dt=.../
   → UPSERT watermark (pg table exporter_watermark) + DELETE exported rows + VACUUM in same TX
   ↓
GCS gs://our-solana-lake-prod/indexer/transfers/ (Bronze Parquet)
   → Spark job jobs/ingestion/build_iceberg.py (or dbt Trino) → Iceberg table
   → Trino lake.solana.transfers / lake.solana_marts.* (backend/docker-compose.yml:6 JDBC, system.register_table)
```

VM (e.g. n2-standard-4, 100GB PD `pd-ssd`, Ubuntu 22.04) runs single `docker compose`:
- `envio-postgres` (image postgres:18, `POSTGRES_PASSWORD=testing`, volume `pgdata:/var/lib/postgresql/data` on PD, `restart: unless-stopped`, healthcheck `pg_isready`)
- `envio-hasura` (optional, `ENVIO_HASURA=false` in prod headless)
- `indexer` container or host `pnpm envio dev` (ENVIO_API_TOKEN, ENVIO_PG_SCHEMA, ENVIO_TUI=false)
- `exporter` container (python:3.11-slim, gcloud ADC via SA, cron)

Alternative host-level: indexer + exporter as systemd services, postgres as compose.

## Exporter Script: jobs/ingestion/export_transfers_to_gcs.py

Spec for production-grade script (write to `Data-pipeline/jobs/ingestion/`):

**Interface**
```
ENV: PG_DSN=postgres://postgres:testing@localhost:5433/envio-dev?options=-c%20search_path%3Dsolana_transfer_raw
     GCS_BUCKET=our-solana-lake-prod
     GCS_PREFIX=indexer/transfers
     BATCH_SIZE=50000
     RETENTION_HOURS=24
     GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp/sa.json (or VM SA)
Usage: python jobs/ingestion/export_transfers_to_gcs.py --once | --daemon --interval 900
```

**Tables**
- Source: `Transfer(id, mint, sender, receiver, source, destination, amount, decimals, normalizedAmount, fee, instruction, program, depth, isInner, slot, txSignature, blockTime)` — handler `src/handlers/transfer.ts:1`
- Watermark: `exporter_watermark(id TEXT PK DEFAULT 'transfers', last_slot BIGINT, last_tx_index INT, last_path TEXT, updated_at TIMESTAMPTZ)` in same PG schema. Init (0,0,"").
- Hasura `envio_chains(progress_block)` for head lag; `GET https://solana.hypersync.xyz/height` for current slot.

**Logic (per run)**
1. Load watermark. Query max slot quickly; if none, exit 0.
2. Stream cursor: `DECLARE cur CURSOR FOR SELECT * FROM Transfer WHERE (slot, split_part(id,'-',3)) > (watermark...) ORDER BY slot, id LIMIT BATCH_SIZE` or simpler `WHERE slot > last_slot OR (slot=last_slot AND txSignature>...)` — deterministic `id` already encodes slot-txIndex-path, so `WHERE id > last_id ORDER BY id` suffices if id monotonic per slot. Prefer `WHERE (slot, id) > (...)`.
3. Fetch Arrow batches via `psycopg` server-side cursor (no OOM). Convert to `pyarrow.Table` with schema: `slot: int64, blockTime: timestamp[s], mint: string, sender: string, receiver: string, amount: int64, decimals: int32, normalizedAmount: double, instruction: string, program: string, depth: int8, txSignature: string`.
4. Partition: group by `dt = to_date(blockTime)` daily. Write each partition to `pyarrow.parquet.write_table` with `compression='zstd', row_group_size=100000` to local `/tmp/uuid/dt=.../part-...parquet`.
5. Upload: `gcsfs` or `google-cloud-storage` `Bucket.blob(_tmp/uuid/...).upload_from_filename`, then compose to final `GCS_PREFIX/dt=YYYY-MM-DD/part-...parquet`. Use `if_generation_match=0` for atomic avoid overwrite. On failure, retry with backoff 3×.
6. On success per batch: `BEGIN; INSERT INTO exporter_watermark ... ON CONFLICT UPDATE; DELETE FROM Transfer WHERE id <= last_exported_id; COMMIT; VACUUM Transfer` (or `DELETE WHERE blockTime < now - RETENTION_HOURS` if lag allowed). Use `DELETE` in same TX as watermark to guarantee exactly-once.
7. Loop next batch until no rows. Log `exported=N, last_slot=S, gcs=gs://...` via `logging` + Cloud Logging. Metrics: `exporter_lag_slots = head - last_slot`, `pg_row_count`.

**Code outline**
```python
import os, psycopg, pyarrow as pa, pyarrow.parquet as pq, gcsfs
PG_DSN = os.environ["PG_DSN"]
fs = gcsfs.GCSFileSystem()
def export_once():
    with psycopg.connect(PG_DSN) as conn:
        cur = conn.cursor()
        cur.execute("SELECT last_slot, last_id FROM exporter_watermark WHERE id='transfers'")
        watermark = cur.fetchone() or (0,"0-0-")
        with conn.cursor(name="export_cur") as scur:
            scur.execute("SELECT * FROM Transfer WHERE id > %s ORDER BY id LIMIT %s", (watermark[1], BATCH_SIZE))
            rows = scur.fetchall() # or fetchmany streamed
            if not rows: return 0
            table = pa.Table.from_pylist([...])
            # partition + write
            for dt, group in groupby:
                path = f"{GCS_BUCKET}/{GCS_PREFIX}/dt={dt}/part-{uuid}.parquet"
                with fs.open(path, "wb") as f: pq.write_table(group, f)
            cur.execute("UPDATE exporter_watermark SET last_slot=%s, last_id=%s", (max_slot, max_id))
            cur.execute("DELETE FROM Transfer WHERE id <= %s", (max_id,))
            conn.commit()
```

**Failure modes & retries**
- HyperSync 403 revoked / 429 rate-limit: indexer stalls, `progress_block` stops. Script checks `envio_chains` head vs watermark; if lag >1h and `x-ratelimit-remaining:0` (curl HyperSync `/query`), alert, don't delete.
- GCS upload partial: `_tmp` prefix is staging; final commit is atomic rename; on crash, orphan `_tmp` cleaned by lifecycle rule (7d).
- Postgres WAL bloat after mass DELETE: schedule `VACUUM (ANALYZE) Transfer` hourly; for prod scale, partition `Transfer` by RANGE(slot) monthly then `DROP PARTITION` instead of DELETE.

## Prod Hardening

**Infra**
- PD-backed `pgdata` volume, snapshot schedule daily, `pg_basebackup` encrypted to GCS. `docker compose` healthchecks, auto-restart, resource limits `mem_limit: 4g` for postgres.
- VM SA with `roles/storage.objectCreator` on `our-solana-lake-prod/indexer/*` only, no SA key file (Workload Identity if GKE). `GOOGLE_APPLICATION_CREDENTIALS` only for local dev via `../../.config/gcloud` relative mount (see backend/docker-compose.yml:21).
- Firewall: Postgres 5433 only localhost, Hasura 8080 not public (`ENVIO_HASURA=false`).

**Observability**
- Systemd timer `OnCalendar=*:0/15` + `journalctl -u exporter`. Exporter logs JSON to stdout → Cloud Logging. Metrics: `transfer_row_count`, `lag_slots`, `parquet_bytes`, `delete_latency`. Alert if `lag_slots > 3600` (15m behind).
- HyperSync: poll `https://solana.hypersync.xyz/height` for head; compare `SELECT progress_block FROM envio_chains`.

**Security & Config**
- `.env` holds `ENVIO_API_TOKEN` (revocable, rotate via https://app.envio.dev/api-tokens), gitignored (`Data-pipeline/indexer/.gitignore:3`). Never commit SA key.
- `ENVIO_PG_SCHEMA=solana_transfer_raw` isolates from other indexers on same PG.
- `full_batch_size: 5000` (config.yaml) tuned to avoid OOM during backfill.

**Scheduling**
- Preferred: Cloud Composer DAG `indexer_export_dag.py` (calls exporter container on GKE) if Data-pipeline already uses Airflow; otherwise systemd timer on VM is sufficient.

**Verification**
```bash
# Postgres live count
docker exec envio-postgres psql -U postgres -d envio-dev -c "SET search_path=solana_transfer_raw; SELECT count(*) FROM Transfer; SELECT * FROM exporter_watermark;"
# GCS
gcloud storage ls gs://our-solana-lake-prod/indexer/transfers/dt=2026-09-18/ --readable-sizes
# Trino after Iceberg register
docker compose exec api python -c "from app.trino_client import run_query; print(run_query('SHOW TABLES FROM lake.solana'))"
```

## When Runs, Report
1. Slot window indexed (`config.yaml start_slot` → `GlobalState` max `slot` / `envio_chains.progress_block`) and whether reached `end_slot` (if set).
2. Per mint/global `transferCount`, `% plain = plainCount/transferCount` would now be derived from Parquet/Iceberg `SELECT instruction, count(*)` since storage switched to per-row Transfer; but pre-export aggregations available via `SELECT mint, count(*) FROM Transfer GROUP BY mint`.
3. `% top-level = depth=0 / total` via `WHERE depth=0`.
