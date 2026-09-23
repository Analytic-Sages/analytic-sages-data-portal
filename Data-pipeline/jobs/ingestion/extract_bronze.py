"""
Bronze extract: BigQuery public dataset -> GCS Parquet via BigQuery EXPORT DATA.
No Spark needed. Server-side export handles any size, no 128MB Jobs inline limit.
Idempotent per (table, date_chunk).

Usage: python extract_bronze.py --table token_transfers --start-date 2026-09-03 --end-date 2026-09-03 --bucket our-solana-lake-prod --billing-project analytic-sages-data-portal
Tables: token_transfers, tokens, transactions, blocks, instructions
"""
import os
import sys
import argparse

BQ_DATASET = "bigquery-public-data.crypto_solana_mainnet_us"
LAKE_BUCKET = os.environ.get("LAKE_BUCKET", "build-solana-lakehouse")

parser = argparse.ArgumentParser(description="Bronze extract BQ -> GCS via EXPORT DATA")
parser.add_argument("--table", default="token_transfers", help="token_transfers | tokens | transactions | blocks | instructions")
parser.add_argument("--start-date", default="2026-09-01")
parser.add_argument("--end-date", default="2026-09-02")
parser.add_argument("--bucket", default=LAKE_BUCKET)
parser.add_argument("--billing-project", default=os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT") or "analytic-sages-data-portal", help="billing project")
parser.add_argument("--snapshot-date", default=None, help="only for tokens: label for snapshot_date= folder, defaults to --start-date")
args = parser.parse_known_args()[0]
table = args.table
start_date = args.start_date
end_date = args.end_date
bucket = args.bucket
billing_project = args.billing_project

BQ_TABLE_MAP = {
    "transfers": "Token Transfers",
    "tokens": "Tokens",
    "transactions": "Transactions",
    "blocks": "Blocks",
    "instructions": "Instructions",
}
bq_table = BQ_TABLE_MAP.get(table, table)
indexer = 'indexer'

print(f"Bronze extract (EXPORT DATA): table={table} -> BQ {BQ_DATASET}.{bq_table} range={start_date} to {end_date} bucket={bucket} billing_project={billing_project}")

try:
    from google.cloud import bigquery as bq_client_lib
    from google.cloud import storage

    bq = bq_client_lib.Client(project=billing_project) if billing_project != "our-project" else bq_client_lib.Client()
    storage_client = storage.Client(project=billing_project) if billing_project != "our-project" else storage.Client()

    # Tokens is metadata: full snapshot, no date filter, no dt= partition.
    # All other tables keep the existing dt= + WHERE block_timestamp path.
    is_snapshot = table.lower() == "tokens"
    if is_snapshot:
        snapshot_date = args.snapshot_date or start_date
        prefix = f"{indexer}/{table}/snapshot_date={snapshot_date}/"
        uri = f"gs://{bucket}/{prefix}part-*.parquet"
        export_sql = f"EXPORT DATA OPTIONS(uri='{uri}', format='PARQUET', overwrite=true) AS SELECT * FROM `{BQ_DATASET}.{bq_table}`"
    else:
        # EXPORT DATA writes Parquet directly to GCS, server-side, no Spark, no responseTooLarge
        prefix = f"{indexer}/{table}/dt={start_date}/"
        uri = f"gs://{bucket}/{prefix}part-*.parquet"
        export_sql = f"EXPORT DATA OPTIONS(uri='{uri}', format='PARQUET', overwrite=true) AS SELECT * FROM `{BQ_DATASET}.{bq_table}` WHERE DATE(block_timestamp) BETWEEN '{start_date}' AND '{end_date}'"
    print(f"Running: {export_sql}")
    job = bq.query(export_sql)
    job.result()
    print(f"EXPORT DATA done job_id={job.job_id}")

    # List written files
    blobs = list(storage_client.list_blobs(bucket, prefix=prefix))
    parquet_blobs = [b for b in blobs if b.name.endswith(".parquet")]
    print(f"Wrote bronze Parquet to gs://{bucket}/{prefix} files={len(parquet_blobs)}")
    for b in parquet_blobs[:10]:
        print(f"  {b.name} {b.size} bytes")
    if len(parquet_blobs) == 0:
        print("No files written, check if source had rows for this date range")

except Exception as e:
    print(f"Bronze extract failed: {e}")
    print("Hint: verify BQ table name. Actual tables: `Token Transfers`, Tokens, Transactions, Blocks")
    print("Hint: billing project needs bigquery.jobs.create and storage.objectAdmin on gs:// bucket for EXPORT DATA")
    raise
