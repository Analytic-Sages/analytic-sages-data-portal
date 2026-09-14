"""Publish Analytic Sages curated Solana tables to BigQuery.

Learner-facing tables (native BigQuery, not Iceberg):
  {project}.solana_curated.transfers
  {project}.solana_curated.transactions
  {project}.solana_curated.token_activity
  {project}.solana_curated.wallet_activity

Modes:
  --source sample   Seed demo rows (no lake required). Good for local proof.
  --source gcs      Load transfers/transactions parquet from bronze GCS paths.
  --source bq-sql   Rebuild activity marts only from existing curated transfers.

Examples:
  python publish_curated_bq.py --source sample --project analytic-sages-data-portal
  python publish_curated_bq.py --source gcs --start-date 2026-09-01 --end-date 2026-09-01
  python publish_curated_bq.py --source bq-sql --project analytic-sages-data-portal
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.curated_contracts import (  # noqa: E402
    CURATED_DATASET,
    CURATED_TABLES,
    TOKEN_ACTIVITY_SQL,
    WALLET_ACTIVITY_SQL,
    create_table_ddl,
    fq_table,
)

DEFAULT_PROJECT = os.environ.get("GCP_PROJECT") or os.environ.get(
    "GOOGLE_CLOUD_PROJECT", "analytic-sages-data-portal"
)
DEFAULT_BUCKET = os.environ.get("LAKE_BUCKET", "our-solana-lake-prod")


def _client(project: str):
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        req = Path(__file__).resolve().parents[1] / "requirements-publish.txt"
        setup = Path(__file__).resolve().parents[2] / "scripts" / "setup_publish_env.sh"
        raise SystemExit(
            "Missing google-cloud-bigquery in this Python environment.\n\n"
            "Use an isolated venv (recommended; avoid conda base):\n"
            f"  bash {setup}\n"
            "  source Data-pipeline/.venv-publish/bin/activate\n\n"
            "Or install into the current env:\n"
            f"  pip install -r {req}\n\n"
            f"Original error: {exc}"
        ) from exc

    try:
        return bigquery.Client(project=project)
    except Exception as exc:
        raise SystemExit(
            "Could not create a BigQuery client.\n\n"
            "Check GCP auth and project access:\n"
            "  gcloud auth application-default login\n"
            f"  gcloud config set project {project}\n"
            "  gcloud auth application-default set-quota-project "
            f"{project}\n\n"
            f"Original error: {exc}"
        ) from exc


def ensure_dataset(client, project: str, dataset: str) -> None:
    from google.cloud import bigquery

    ds_id = f"{project}.{dataset}"
    ds = bigquery.Dataset(ds_id)
    ds.location = os.environ.get("BQ_LOCATION", "US")
    ds.description = "Analytic Sages curated Solana datasets for learners"
    client.create_dataset(ds, exists_ok=True)
    print(f"Dataset ready: {ds_id}")


def recreate_native_tables(client, project: str, dataset: str, tables: tuple[str, ...]) -> None:
    """Drop and recreate as native BQ tables (avoids Iceberg TRUNCATE limits)."""
    for table in tables:
        fq = fq_table(project, table, dataset)
        client.delete_table(fq, not_found_ok=True)
        client.query(create_table_ddl(project, table, dataset)).result()
        print(f"Native table ready: {fq}")


def ensure_base_tables(client, project: str, dataset: str) -> None:
    recreate_native_tables(client, project, dataset, ("transfers", "transactions"))


def build_activity_marts(client, project: str, dataset: str) -> None:
    for label, sql in (
        ("token_activity", TOKEN_ACTIVITY_SQL),
        ("wallet_activity", WALLET_ACTIVITY_SQL),
    ):
        job = client.query(sql.format(project=project, dataset=dataset))
        job.result()
        print(f"Built mart: {fq_table(project, label, dataset)} job={job.job_id}")


def seed_sample(client, project: str, dataset: str) -> None:
    """Insert a small curated sample so Lab 01 works without the lake."""
    now = datetime.now(timezone.utc)
    transfers = []
    mints = [
        ("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 6),  # USDC
        ("So11111111111111111111111111111111111111112", 9),  # wSOL
    ]
    wallets = [
        "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
        "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
        "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH",
    ]

    for i in range(40):
        mint, decimals = mints[i % 2]
        raw = (i + 1) * 10**decimals * (40 - i)
        amount_ui = float(raw) / (10**decimals)
        ts = now - timedelta(hours=i * 3)
        transfers.append(
            {
                "block_slot": 280_000_000 - i,
                "block_timestamp": ts.isoformat().replace("+00:00", "Z"),
                "tx_signature": f"SampleSig{'A' * 40}{i:02d}",
                "source": wallets[i % len(wallets)],
                "destination": wallets[(i + 1) % len(wallets)],
                "mint": mint,
                "amount": str(raw),
                "decimals": decimals,
                "amount_ui": amount_ui,
                "fee": "5000",
                "memo": None,
                "transfer_type": "transfer",
                "_published_at": now.isoformat().replace("+00:00", "Z"),
            }
        )

    transactions = []
    for i in range(25):
        ts = now - timedelta(hours=i * 4)
        transactions.append(
            {
                "block_slot": 280_000_000 - i,
                "block_timestamp": ts.isoformat().replace("+00:00", "Z"),
                "signature": f"SampleTx{'B' * 40}{i:02d}",
                "tx_index": i,
                "fee": str(5000 + i * 100),
                "status": "success" if i % 7 else "failure",
                "err": None if i % 7 else "InstructionError",
                "compute_units_consumed": str(50_000 + i * 1000),
                "_published_at": now.isoformat().replace("+00:00", "Z"),
            }
        )

    # Fresh native tables (no TRUNCATE; avoids Iceberg DML limits)
    recreate_native_tables(client, project, dataset, ("transfers", "transactions"))

    t_ref = client.dataset(dataset).table("transfers")
    errors = client.insert_rows_json(t_ref, transfers)
    if errors:
        raise RuntimeError(f"transfers insert errors: {errors[:3]}")
    print(f"Seeded transfers rows={len(transfers)}")

    x_ref = client.dataset(dataset).table("transactions")
    errors = client.insert_rows_json(x_ref, transactions)
    if errors:
        raise RuntimeError(f"transactions insert errors: {errors[:3]}")
    print(f"Seeded transactions rows={len(transactions)}")


def load_from_gcs(
    client,
    project: str,
    dataset: str,
    bucket: str,
    start_date: str,
    end_date: str,
) -> None:
    """Load bronze parquet for transfers/transactions into curated BQ tables."""
    from google.cloud import bigquery

    for logical, bronze_names in (
        ("transfers", ("transfers", "token_transfers")),
        ("transactions", ("transactions",)),
    ):
        uris: list[str] = []
        for name in bronze_names:
            d0 = datetime.strptime(start_date, "%Y-%m-%d").date()
            d1 = datetime.strptime(end_date, "%Y-%m-%d").date()
            cur = d0
            while cur <= d1:
                uris.append(f"gs://{bucket}/bronze/{name}/dt={cur.isoformat()}/*.parquet")
                cur += timedelta(days=1)

        loaded = 0
        staging = f"{project}.{dataset}._staging_{logical}"
        client.delete_table(staging, not_found_ok=True)
        for uri in uris:
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.PARQUET,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=True,
            )
            try:
                load_job = client.load_table_from_uri(uri, staging, job_config=job_config)
                load_job.result()
                loaded += 1
            except Exception as exc:
                print(f"Skip missing/unreadable {uri}: {exc}")

        if loaded == 0:
            print(f"No GCS files loaded for {logical}; skipping transform")
            continue

        if logical == "transfers":
            transform = f"""
            INSERT INTO `{project}.{dataset}.transfers`
            SELECT
              CAST(COALESCE(block_slot, slot) AS INT64) AS block_slot,
              CAST(block_timestamp AS TIMESTAMP) AS block_timestamp,
              CAST(tx_signature AS STRING) AS tx_signature,
              CAST(source AS STRING) AS source,
              CAST(destination AS STRING) AS destination,
              CAST(mint AS STRING) AS mint,
              CAST(value AS NUMERIC) AS amount,
              CAST(decimals AS INT64) AS decimals,
              SAFE_DIVIDE(CAST(value AS FLOAT64), POW(10, CAST(decimals AS FLOAT64))) AS amount_ui,
              CAST(fee AS NUMERIC) AS fee,
              CAST(memo AS STRING) AS memo,
              CAST(transfer_type AS STRING) AS transfer_type,
              CURRENT_TIMESTAMP() AS _published_at
            FROM `{staging}`
            WHERE block_timestamp IS NOT NULL
            """
        else:
            transform = f"""
            INSERT INTO `{project}.{dataset}.transactions`
            SELECT
              CAST(COALESCE(block_slot, slot) AS INT64) AS block_slot,
              CAST(block_timestamp AS TIMESTAMP) AS block_timestamp,
              CAST(signature AS STRING) AS signature,
              CAST(`index` AS INT64) AS tx_index,
              CAST(fee AS NUMERIC) AS fee,
              CAST(status AS STRING) AS status,
              CAST(err AS STRING) AS err,
              CAST(compute_units_consumed AS NUMERIC) AS compute_units_consumed,
              CURRENT_TIMESTAMP() AS _published_at
            FROM `{staging}`
            WHERE block_timestamp IS NOT NULL
            """
        client.query(transform).result()
        print(f"GCS publish complete for {logical} staging_loads={loaded}")
        client.delete_table(staging, not_found_ok=True)


def write_publish_manifest(project: str, dataset: str, source: str, tables: list[str]) -> Path:
    out_dir = Path(__file__).resolve().parents[2] / "checkpoints" / "publish"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "curated_bq.json"
    payload = {
        "published_at": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "dataset": dataset,
        "source": source,
        "tables": [fq_table(project, t, dataset) for t in tables],
        "freshness_note": "Updated from Analytic Sages curated publish job",
    }
    path.write_text(json.dumps(payload, indent=2))
    print(f"Manifest: {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish curated Solana tables to BigQuery")
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--dataset", default=CURATED_DATASET)
    parser.add_argument("--source", choices=("sample", "gcs", "bq-sql"), default="sample")
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()

    client = _client(args.project)
    ensure_dataset(client, args.project, args.dataset)

    if args.source == "gcs":
        ensure_base_tables(client, args.project, args.dataset)

    if args.source == "sample":
        seed_sample(client, args.project, args.dataset)
        build_activity_marts(client, args.project, args.dataset)
    elif args.source == "gcs":
        if not args.start_date or not args.end_date:
            parser.error("--source gcs requires --start-date and --end-date")
        load_from_gcs(
            client,
            args.project,
            args.dataset,
            args.bucket,
            args.start_date,
            args.end_date,
        )
        build_activity_marts(client, args.project, args.dataset)
    else:
        build_activity_marts(client, args.project, args.dataset)

    tables = list(CURATED_TABLES.keys())
    write_publish_manifest(args.project, args.dataset, args.source, tables)
    print("Publish complete:")
    for t in tables:
        print(f"  - {fq_table(args.project, t, args.dataset)}")


if __name__ == "__main__":
    main()
