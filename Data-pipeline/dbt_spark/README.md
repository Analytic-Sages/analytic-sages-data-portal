# dbt-spark transform layer (solana_lakehouse)

dbt project that reads the Iceberg tables built by the Bronze to Iceberg
ingestion pipeline (`jobs/ingestion/build_iceberg.py`, Hadoop catalog
`iceberg`, warehouse `gs://our-solana-lake-prod/warehouse`) and produces
staging views plus marts. It depends on those tables already existing.

## Setup

```bash
pip install -r requirements.txt --break-system-packages
export DBT_PROFILES_DIR=$(pwd)
```

## Run

1. On the Dataproc master node: `./start_thrift_server.sh`
2. From wherever dbt runs: `export THRIFT_HOST=<master-ip>`
3. Verify: `dbt debug --target dev`
4. Build: `dbt run`

## Catalog naming (read this)

dbt-spark 1.11 relations support only two-level names, and the adapter
raises `Cannot set database in spark!` on any 3-level reference. So:

- Staging READS use the `iceberg_relation('solana', '<table>')` macro,
  which emits raw `iceberg.solana.<table>` text (no relation object).
- All WRITES (staging views, marts tables) use plain two-level names and
  resolve through the Thrift server's default `spark_catalog`, which
  `start_thrift_server.sh` points at the same Iceberg HadoopCatalog and
  warehouse. Nothing lands in Derby.
- Verify with `dbt compile`: reads show `iceberg.solana.<table>`, writes
  show `<schema>_<custom>.<model>`.

## Known limitation: MERGE / incremental

Marts use full-refresh `table` materialization to sidestep dbt-spark `merge`
limits on Iceberg. Test `merge` on a throwaway table before using it in marts.

## Resulting schema names

Staging views land in `iceberg.solana_staging`, the mart in
`iceberg.solana_marts` (dbt appends the configured schema). Confirm the
actual names after the first run. All data stays under
`gs://our-solana-lake-prod/warehouse`.
