#!/usr/bin/env bash
# Starts HiveThriftServer2 on the Dataproc master with EXACTLY the same
# Spark/Iceberg/GCS config as get_spark() in jobs/lib/spark_session.py
# (catalog name `iceberg`, HadoopCatalog, warehouse
# gs://our-solana-lake-prod/warehouse, same jar versions).
#
# KEEP IN SYNC: if spark_session.py changes its catalog config (warehouse
# path, jar versions, catalog name), update this script to match or dbt
# will read/write against a different or broken catalog view.
#
# Run on the Dataproc master node, then from wherever dbt runs:
#   export THRIFT_HOST=<master-ip>
#   export DBT_PROFILES_DIR=$(pwd)
#   dbt debug --target dev
set -euo pipefail

JARS="org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.6.1,\
com.google.cloud.bigdataoss:gcs-connector:hadoop3-2.2.11,\
org.apache.iceberg:iceberg-gcp-bundle:1.6.1,\
org.scala-lang:scala-library:2.12.18"

SPARK_HOME="${SPARK_HOME:-/usr/lib/spark}"
THRIFT_JAR=$(ls "${SPARK_HOME}"/jars/spark-hive-thriftserver*.jar 2>/dev/null | head -n 1)

exec spark-submit \
  --master yarn \
  --class org.apache.spark.sql.hive.thriftserver.HiveThriftServer2 \
  --packages "${JARS}" \
  --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
  --conf spark.sql.catalog.iceberg=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.iceberg.catalog-impl=org.apache.iceberg.hadoop.HadoopCatalog \
  --conf spark.sql.catalog.iceberg.warehouse=gs://our-solana-lake-prod/warehouse \
  --conf spark.sql.catalog.iceberg.io-impl=org.apache.iceberg.hadoop.HadoopFileIO \
  --conf spark.sql.catalog.spark_catalog=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.spark_catalog.catalog-impl=org.apache.iceberg.hadoop.HadoopCatalog \
  --conf spark.sql.catalog.spark_catalog.warehouse=gs://our-solana-lake-prod/warehouse \
  --conf spark.sql.catalog.spark_catalog.io-impl=org.apache.iceberg.hadoop.HadoopFileIO \
  --conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem \
  --conf spark.hadoop.fs.AbstractFileSystem.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS \
  --hiveconf hive.server2.thrift.port=10000 \
  --hiveconf hive.server2.thrift.bind.host=0.0.0.0 \
  "${THRIFT_JAR}"
