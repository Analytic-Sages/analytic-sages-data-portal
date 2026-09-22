"""
Bronze -> Iceberg (idempotent). Hadoop catalog on GCS.

Event tables (day partitioned, per-day reload):
  python build_iceberg.py --table transfers --start-date 2025-04-01 --end-date 2025-04-08

Token metadata (full snapshot, unpartitioned, keyed by mint):
  python build_iceberg.py --table tokens --snapshot-date 2026-09-13
"""
import sys, os, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pyspark.sql import functions as F
from lib.spark_session import get_spark, CATALOG_NAME
from lib.watermarks import write_watermark
from lib.schemas import MERGE_KEYS

GCS_PREFIX_DEFAULT = 'indexer'
parser = argparse.ArgumentParser(description="Bronze -> Iceberg")
parser.add_argument("--table", required=True, help="transfers | tokens | transactions | blocks")
parser.add_argument("--start-date", default=None, help="event tables: chunk start (also fallback label for tokens)")
parser.add_argument("--end-date", default=None, help="event tables: chunk end")
parser.add_argument("--snapshot-date", default=None, help="tokens only: snapshot_date= folder to load")
parser.add_argument("--bucket", default=os.environ.get("LAKE_BUCKET", "our-solana-lake-prod"))
parser.add_argument("--gcs-prefix", default=GCS_PREFIX_DEFAULT)
args = parser.parse_args()

table = args.table.lower()
bucket = args.bucket
catalog = CATALOG_NAME
db = "solana"

is_snapshot = table == "tokens"
snapshot_date = None
start_date = None
end_date = None

if is_snapshot:
    snapshot_date = args.snapshot_date or args.start_date
    if not snapshot_date:
        parser.error("tokens needs --snapshot-date YYYY-MM-DD (or --start-date as fallback)")
    print(f"Iceberg snapshot load: table={table} snapshot={snapshot_date} catalog={catalog}.{db}")
    spark = get_spark(app_name=f"iceberg-{table}-{snapshot_date}")
else:
    start_date = args.start_date
    end_date = args.end_date
    if not start_date or not end_date:
        parser.error("event tables need --start-date and --end-date YYYY-MM-DD")
    print(f"Iceberg MERGE: table={table} range={start_date} to {end_date} catalog={catalog}.{db}")
    spark = get_spark(app_name=f"iceberg-{table}-{start_date}")

spark.sql(f"CREATE DATABASE IF NOT EXISTS {catalog}.{db}")

bronze_base = f"gs://{bucket}/{args.gcs_prefix}/{table}"

try:
    if is_snapshot:
        # Tokens: one full snapshot folder, no date filter, no dt= path.
        src_path = f"{bronze_base}/snapshot_date={snapshot_date}"
        src = spark.read.parquet(src_path)
    else:
        # Backfill loop: handle range start_date..end_date inclusive in one Spark session
        from datetime import datetime, timedelta
        from pyspark.sql.types import TimestampType, DecimalType

        def _load_dt(dt_str):
            p = f"{bronze_base}/dt={dt_str}"
            try:
                df = spark.read.parquet(p)
                print(f"Loaded dt={dt_str} rows={df.count()}")
                return df
            except Exception as e:
                print(f"dt={dt_str} not found/empty, skipping: {e}")
                return None

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end_dt - start_dt).days + 1

        # If single day, keep previous fast path; else loop
        if days == 1:
            src_path = f"{bronze_base}/dt={start_date}"
            try:
                src = spark.read.parquet(src_path)
            except Exception:
                print(f"dt folder not found, reading {bronze_base} with timestamp filter")
                src = spark.read.parquet(bronze_base).filter(
                    (F.to_date(F.col("block_timestamp")) >= F.lit(start_date)) &
                    (F.to_date(F.col("block_timestamp")) <= F.lit(end_date))
                )
            src_list = [src] if src.count() > 0 else []
        else:
            print(f"Backfill loop: {days} days {start_date} -> {end_date}")
            src_list = []
            for i in range(days):
                dt = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
                df = _load_dt(dt)
                if df is not None and df.count() > 0:
                    # Handle alias/casts per-day before union
                    if "slot" in df.columns and "block_slot" not in df.columns:
                        df = df.withColumnRenamed("slot", "block_slot")
                    if "block_timestamp" in df.columns and dict(df.dtypes)["block_timestamp"] in ("bigint", "long"):
                        df = df.withColumn("block_timestamp", F.from_unixtime(F.col("block_timestamp")).cast(TimestampType()))
                    if "value" in df.columns and dict(df.dtypes)["value"] in ("bigint", "long"):
                        df = df.withColumn("value", F.col("value").cast(DecimalType(38, 9)))
                    if "decimals" in df.columns and dict(df.dtypes)["decimals"] in ("int", "bigint", "long"):
                        df = df.withColumn("decimals", F.col("decimals").cast(DecimalType(38, 9)))
                    if "fee" in df.columns and dict(df.dtypes)["fee"] in ("bigint", "long"):
                        df = df.withColumn("fee", F.col("fee").cast(DecimalType(38, 9)))
                    if "fee_decimals" in df.columns and dict(df.dtypes)["fee_decimals"] in ("int", "bigint", "long"):
                        df = df.withColumn("fee_decimals", F.col("fee_decimals").cast(DecimalType(38, 9)))
                    if "id" in df.columns:
                        df = df.drop("id")
                    src_list.append(df)
            if not src_list:
                print("No bronze rows for entire range, skipping")
                sys.exit(0)
            # Union all days
            src = src_list[0]
            for df in src_list[1:]:
                src = src.unionByName(df, allowMissingColumns=True)

        # Handle BQ column alias: Blocks has slot not block_slot
        if "slot" in src.columns and "block_slot" not in src.columns:
            src = src.withColumnRenamed("slot", "block_slot")
        if "slot_index" in src.columns and "index" not in src.columns:
            pass

        # Env indexer writes block_timestamp as bigint (unix secs) and value as bigint; Iceberg expects Timestamp/Decimal
        # Cast to match TOKEN_TRANSFERS_SCHEMA if needed (safe when source already correct type) — for single-day path
        from pyspark.sql.types import TimestampType, DecimalType
        if "block_timestamp" in src.columns:
            if dict(src.dtypes)["block_timestamp"] in ("bigint", "long"):
                src = src.withColumn("block_timestamp", F.from_unixtime(F.col("block_timestamp")).cast(TimestampType()))
        if "value" in src.columns and dict(src.dtypes)["value"] in ("bigint", "long"):
            src = src.withColumn("value", F.col("value").cast(DecimalType(38, 9)))
        if "decimals" in src.columns and dict(src.dtypes)["decimals"] in ("int", "bigint", "long"):
            src = src.withColumn("decimals", F.col("decimals").cast(DecimalType(38, 9)))
        if "fee" in src.columns and dict(src.dtypes)["fee"] in ("bigint", "long"):
            src = src.withColumn("fee", F.col("fee").cast(DecimalType(38, 9)))
        if "fee_decimals" in src.columns and dict(src.dtypes)["fee_decimals"] in ("int", "bigint", "long"):
            src = src.withColumn("fee_decimals", F.col("fee_decimals").cast(DecimalType(38, 9)))
        # Drop PG-only id if present (not in lake schema)
        if "id" in src.columns:
            src = src.drop("id")

        src = src.withColumn("_ingested_at", F.current_timestamp())
        row_count = src.count()
        print(f"Bronze rows to merge (total range): {row_count}")
        if row_count == 0:
            print("No rows, skipping MERGE")
            sys.exit(0)

        expected_keys = MERGE_KEYS.get(table, ["block_slot"])
        for k in expected_keys:
            if k not in src.columns:
                raise ValueError(f"Schema drift: expected merge key {k} not in bronze columns {src.columns}")

        src.createOrReplaceTempView("src_view")
        on_clause = " AND ".join([f"t.{k} = s.{k}" for k in expected_keys])
        target = f"{catalog}.{db}.{table}"

        try:
            spark.sql(f"DESCRIBE TABLE {target}")
            table_exists = True
        except Exception:
            table_exists = False

        if is_snapshot:
            src.writeTo(target).createOrReplace()
            print(f"Snapshot load into unpartitioned {target} complete rows={row_count}")
        elif not table_exists:
            print(f"Target {target} does not exist, creating with initial load partitioned by days(block_timestamp)")
            src.writeTo(target).partitionedBy(F.days(F.col("block_timestamp"))).createOrReplace()
            print(f"Created partitioned {target} with {row_count} rows")
        else:
            # Idempotent range reload: overwritePartitions handles all day partitions present in src
            src.writeTo(target).overwritePartitions()
            print(f"Overwrite partitions into {target} complete for range {start_date}..{end_date}")

    # Update watermark
    if is_snapshot:
        max_slot = None
        if "block_slot" in src.columns:
            max_slot = src.agg(F.max("block_slot").alias("m")).collect()[0]["m"]
        write_watermark(table, max_slot, snapshot_date)
        print(f"Done. Watermark: last_slot={max_slot} snapshot_date={snapshot_date}")
    else:
        max_slot = src.agg(F.max("block_slot").alias("m")).collect()[0]["m"]
        write_watermark(table, max_slot, end_date)
        print(f"Done. Watermark: last_slot={max_slot} last_block_date={end_date}")

except Exception as e:
    print(f"Iceberg MERGE failed: {e}")
    raise
