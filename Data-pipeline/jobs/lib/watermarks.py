"""
Watermark read/write for incremental ingestion.
Stored as JSON at gs://<bucket>/checkpoints/watermarks/{table}.json
Local fallback uses ./checkpoints/ for testing without GCS.
"""
import json
import os
from datetime import date

try:
    from google.cloud import storage
    HAS_GCS = True
except ImportError:
    HAS_GCS = False

LOCAL_CHECKPOINT_DIR = os.environ.get("CHECKPOINT_DIR", "checkpoints/watermarks")
GCS_BUCKET = os.environ.get("LAKE_BUCKET", "")
GCS_PREFIX = "checkpoints/watermarks"


def _local_path(table):
    return os.path.join(LOCAL_CHECKPOINT_DIR, f"{table}.json")


def _gcs_path(table):
    return f"{GCS_PREFIX}/{table}.json"


def read_watermark(table):
    """Return dict {last_slot, last_block_date} or None if not found."""
    if GCS_BUCKET and HAS_GCS:
        try:
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(_gcs_path(table))
            if blob.exists():
                return json.loads(blob.download_as_text())
        except Exception as e:
            print(f"GCS watermark read failed, falling back to local: {e}")

    path = _local_path(table)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def write_watermark(table, last_slot, last_block_date):
    """Persist watermark. Writes to GCS if configured, always to local."""
    payload = {
        "last_slot": int(last_slot) if last_slot is not None else None,
        "last_block_date": str(last_block_date) if last_block_date else None,
    }

    # Always write local copy
    os.makedirs(LOCAL_CHECKPOINT_DIR, exist_ok=True)
    with open(_local_path(table), "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Watermark written local: {payload}")

    # Also write to GCS if configured
    if GCS_BUCKET and HAS_GCS:
        try:
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(_gcs_path(table))
            blob.upload_from_string(json.dumps(payload), content_type="application/json")
            print(f"Watermark written gs://{GCS_BUCKET}/{_gcs_path(table)}")
        except Exception as e:
            print(f"GCS watermark write failed: {e}")

    return payload


def chunk_dates(start_date, end_date, chunk_days=7):
    """Yield (chunk_start, chunk_end) date strings for backfill parallelism."""
    from datetime import datetime, timedelta

    cur = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    delta = timedelta(days=chunk_days)
    while cur <= end:
        chunk_end = min(cur + delta - timedelta(days=1), end)
        yield (cur.isoformat(), chunk_end.isoformat())
        cur = chunk_end + timedelta(days=1)
