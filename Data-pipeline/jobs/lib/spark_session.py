"""
Shared Spark session builder for Solana Lakehouse.
Single place to switch catalog impl (Hadoop for local).
"""
import os
from pyspark.sql import SparkSession
BQ_PROJECT = "analytic-sages-data-portal"
BQ_DATASET = "bigquery-public-data.crypto_solana_mainnet_us"
WAREHOUSE = "gs://build-solana-lakehouse/warehouse"
CATALOG_NAME = "iceberg"
SCRATCH_PROJECT = "analytic-sages-data-portal"
SCRATCH_DATASET = "spark_scratch"


def get_spark(app_name="solana-lakehouse", shuffle_partitions="512"):
    """Return a SparkSession configured for Iceberg HadoopCatalog via GCS."""
    # Dataproc sets DATAPROC_IMAGE_VERSION, local WSL does not
    is_dataproc = (
        os.environ.get("DATAPROC_IMAGE_VERSION") is not None
        or os.environ.get("DATAPROC_VERSION") is not None
        or os.path.exists("/etc/dataproc")
        or os.path.exists("/usr/local/share/google/dataproc")
    )
    builder = (
        SparkSession.builder.appName(app_name)
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(
            f"spark.sql.catalog.{CATALOG_NAME}",
            "org.apache.iceberg.spark.SparkCatalog",
        )
    )
    builder = (
        builder.config(
            f"spark.sql.catalog.{CATALOG_NAME}.catalog-impl",
            "org.apache.iceberg.hadoop.HadoopCatalog",
        )
        .config(f"spark.sql.catalog.{CATALOG_NAME}.warehouse", WAREHOUSE)
        .config(
            f"spark.sql.catalog.{CATALOG_NAME}.io-impl",
            "org.apache.iceberg.hadoop.HadoopFileIO",
        )
    )
    builder = builder.config(
            "spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,"
            "com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,"
            "org.apache.iceberg:iceberg-gcp-bundle:1.6.1,"
            "org.scala-lang:scala-library:2.12.18",
        ).config(
            "spark.hadoop.fs.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem",
        ).config(
            "spark.hadoop.fs.AbstractFileSystem.gs.impl",
            "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS",
        ).config("spark.sql.shuffle.partitions", shuffle_partitions)
    # Local WSL uses ADC, Dataproc uses VM service account
    if not is_dataproc:
        builder = builder.config(
            "spark.hadoop.google.cloud.auth.service.account.enable", "false"
        )
    return builder.getOrCreate()
