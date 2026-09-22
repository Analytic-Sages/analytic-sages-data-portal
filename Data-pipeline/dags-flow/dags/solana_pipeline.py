"""
Solana pipeline: export every 5m, Iceberg/dbt daily + manual trigger.
Network fix: solana-net external (docker network connect solana-net envio-postgres)
PG_DSN via solana-net DNS.
"""
from airflow.decorators import dag
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta

PROJECT = "analytic-sages-data-portal"
REGION = "us-central1"
BUCKET = "build-solana-lakehouse" #our-solana-lake-prod"
GCS_PREFIX = "indexer/transfers"  # exporter writes here
GCS_PREFIX_BASE = "indexer"  # build_iceberg appends /{table} → indexer/transfers
PG_DSN = "postgres://postgres:testing@envio-postgres:5432/envio-dev?options=-c%20search_path%3Dgeneral_transfer_raw"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="solana_export_transfers",
    start_date=datetime(2026, 9, 16),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["solana", "export"],
    doc_md="Every 5m: Postgres Transfer → GCS dt= daily Parquet (no id, drops before write).",
)
def solana_export_transfers():
    BashOperator(
        task_id="export_transfers_to_gcs",
        bash_command=(
            'python /opt/airflow/ingestion/export_transfers_to_gcs.py'
        ),
        env={
            "PG_DSN": "{{ var.value.get('PG_DSN', '" + PG_DSN + "') }}",
            "GCS_BUCKET": BUCKET,
            "GCS_PREFIX": GCS_PREFIX,
        },
    )


@dag(
    dag_id="solana_daily_lakehouse",
    start_date=datetime(2026, 9, 16),
    schedule="0 2 * * *",
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["solana", "iceberg", "dbt"],
    doc_md="Daily 02:00 UTC: build_iceberg transfers dt={{ds}} → Iceberg, then dbt. Also manually triggerable via UI → Trigger DAG.",
)
def solana_daily_lakehouse():
    submit_iceberg = BashOperator(
        task_id="submit_build_iceberg",
        bash_command=(
            "gcloud dataproc batches submit pyspark "
            "gs://{{ params.bucket }}/code/jobs/ingestion/build_iceberg.py "
            "--project={{ params.project }} --region={{ params.region }} --version=2.1 "
            "--py-files=gs://{{ params.bucket }}/code/jobs-lib-2.zip "
            "--properties=^#^spark.jars.packages=org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,org.apache.iceberg:iceberg-gcp-bundle:1.6.1 "
            "-- --table transfers --start-date {{ ds }} --end-date {{ ds }} --bucket {{ params.bucket }} --gcs-prefix {{ params.gcs_prefix }}"
        ),
        params={"project": PROJECT, "region": REGION, "bucket": BUCKET, "gcs_prefix": GCS_PREFIX_BASE},
    )

    submit_dbt = BashOperator(
        task_id="submit_dbt_transform",
        bash_command=(
            "gcloud dataproc batches submit pyspark "
            "gs://{{ params.bucket }}/code/run_dbt_v2.py "
            "--project={{ params.project }} --region={{ params.region }} --version=2.1 "
            "--archives=gs://{{ params.bucket }}/code/dbt_spark_v2.zip#dbt_spark_v2 "
            "--properties=^#^spark.jars.packages=org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,org.apache.iceberg:iceberg-gcp-bundle:1.6.1"
            "#spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
            "#spark.sql.catalog.spark_catalog=org.apache.iceberg.spark.SparkCatalog"
            "#spark.sql.catalog.spark_catalog.type=hadoop"
            "#spark.sql.catalog.spark_catalog.warehouse=gs://{{ params.bucket }}/warehouse"
            "#spark.sql.catalog.spark_catalog.io-impl=org.apache.iceberg.hadoop.HadoopFileIO"
            "#spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog"
            "#spark.sql.catalog.iceberg.type=hadoop"
            "#spark.sql.catalog.iceberg.warehouse=gs://{{ params.bucket }}/warehouse"
            "#spark.sql.catalog.iceberg.io-impl=org.apache.iceberg.hadoop.HadoopFileIO"
            "#spark.sql.warehouse.dir=gs://{{ params.bucket }}/warehouse "
        ),
        params={"project": PROJECT, "region": REGION, "bucket": BUCKET},
    )

    submit_iceberg >> submit_dbt


export_dag = solana_export_transfers()
daily_dag = solana_daily_lakehouse()


@dag(
    dag_id="solana_backfill",
    start_date=datetime(2026, 9, 16),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    params={
        "start_date": "2026-09-16",
        "end_date": "2026-09-16",
    },
    tags=["solana", "backfill"],
    doc_md="Manual backfill: Trigger with conf {\"start_date\": \"2026-08-01\", \"end_date\": \"2026-09-16\"} → one batches submit looping over range in build_iceberg.py (vs 30 daily runs).",
)
def solana_backfill():
    submit_backfill = BashOperator(
        task_id="submit_backfill_iceberg",
        bash_command=(
            "gcloud dataproc batches submit pyspark "
            "gs://{{ params.bucket }}/code/jobs/ingestion/build_iceberg.py "
            "--project={{ params.project }} --region={{ params.region }} --version=2.1 "
            "--py-files=gs://{{ params.bucket }}/code/jobs-lib.zip "
            "--properties=^#^spark.jars.packages=org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,org.apache.iceberg:iceberg-gcp-bundle:1.6.1 "
            "-- --table transfers --start-date {{ dag_run.conf.get('start_date', params.start_date) }} --end-date {{ dag_run.conf.get('end_date', params.end_date) }} --bucket {{ params.bucket }} --gcs-prefix {{ params.gcs_prefix }}"
        ),
        params={"project": PROJECT, "region": REGION, "bucket": BUCKET, "gcs_prefix": GCS_PREFIX_BASE, "start_date": "2026-09-16", "end_date": "2026-09-16"},
    )

    # optional: chain dbt after backfill as well
    submit_dbt_after = BashOperator(
        task_id="submit_dbt_after_backfill",
        bash_command=(
            "gcloud dataproc batches submit pyspark "
            "gs://{{ params.bucket }}/code/run_dbt_v2.py "
            "--project={{ params.project }} --region={{ params.region }} --version=2.1 "
            "--archives=gs://{{ params.bucket }}/code/dbt_spark_v2.zip#dbt_spark_v2 "
            "--properties=^#^spark.jars.packages=org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,org.apache.iceberg:iceberg-gcp-bundle:1.6.1"
            "#spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions"
            "#spark.sql.catalog.spark_catalog=org.apache.iceberg.spark.SparkCatalog"
            "#spark.sql.catalog.spark_catalog.type=hadoop"
            "#spark.sql.catalog.spark_catalog.warehouse=gs://{{ params.bucket }}/warehouse"
            "#spark.sql.catalog.spark_catalog.io-impl=org.apache.iceberg.hadoop.HadoopFileIO"
            "#spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog"
            "#spark.sql.catalog.iceberg.type=hadoop"
            "#spark.sql.catalog.iceberg.warehouse=gs://{{ params.bucket }}/warehouse"
            "#spark.sql.catalog.iceberg.io-impl=org.apache.iceberg.hadoop.HadoopFileIO"
            "#spark.sql.warehouse.dir=gs://{{ params.bucket }}/warehouse "
        ),
        params={"project": PROJECT, "region": REGION, "bucket": BUCKET},
    )

    submit_backfill >> submit_dbt_after


backfill_dag = solana_backfill()
