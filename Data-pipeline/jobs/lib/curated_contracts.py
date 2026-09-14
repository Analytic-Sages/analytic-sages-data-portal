"""Learner-facing curated table contracts for BigQuery publish.

Physical location (default):
  `{project}.solana_curated.{table}`
  e.g. analytic-sages-data-portal.solana_curated.token_transfers

Separate from lake/Iceberg dataset `solana` so curated learner tables
are native BigQuery tables (TRUNCATE / DML friendly).
"""

from __future__ import annotations

CURATED_DATASET = "solana_curated"

# Columns learners see (order matters for docs + CREATE TABLE).
CURATED_TABLES: dict[str, dict] = {
    "token_transfers": {
        "description": "One row per token transfer event.",
        "partition_field": "block_timestamp",
        "partition_type": "DAY",
        "cluster_fields": ["mint", "source", "destination"],
        "columns": [
            ("block_slot", "INT64", "Solana slot"),
            ("block_timestamp", "TIMESTAMP", "Block time (UTC)"),
            ("tx_signature", "STRING", "Transaction signature"),
            ("source", "STRING", "Sender wallet"),
            ("destination", "STRING", "Receiver wallet"),
            ("mint", "STRING", "Token mint address"),
            ("amount", "NUMERIC", "Transfer amount (raw units)"),
            ("decimals", "INT64", "Token decimals"),
            ("amount_ui", "FLOAT64", "Human-readable amount"),
            ("fee", "NUMERIC", "Transfer fee if any"),
            ("memo", "STRING", "Optional memo"),
            ("transfer_type", "STRING", "Transfer type"),
            ("_published_at", "TIMESTAMP", "When Analytic Sages published this row"),
        ],
    },
    "transactions": {
        "description": "One row per Solana transaction.",
        "partition_field": "block_timestamp",
        "partition_type": "DAY",
        "cluster_fields": ["signature", "status"],
        "columns": [
            ("block_slot", "INT64", "Solana slot"),
            ("block_timestamp", "TIMESTAMP", "Block time (UTC)"),
            ("signature", "STRING", "Transaction signature"),
            ("tx_index", "INT64", "Index within the block"),
            ("fee", "NUMERIC", "Fee paid (lamports)"),
            ("status", "STRING", "success or failure"),
            ("err", "STRING", "Error message if failed"),
            ("compute_units_consumed", "NUMERIC", "Compute units used"),
            ("_published_at", "TIMESTAMP", "When Analytic Sages published this row"),
        ],
    },
    "token_activity": {
        "description": "One row per token per day with transfer activity.",
        "partition_field": "block_date",
        "partition_type": "DAY",
        "cluster_fields": ["mint"],
        "columns": [
            ("block_date", "DATE", "UTC calendar day"),
            ("mint", "STRING", "Token mint address"),
            ("transfer_count", "INT64", "Number of transfers that day"),
            ("total_volume", "FLOAT64", "Sum of amount_ui that day"),
            ("unique_senders", "INT64", "Distinct sending wallets"),
            ("unique_receivers", "INT64", "Distinct receiving wallets"),
            ("_published_at", "TIMESTAMP", "When Analytic Sages published this row"),
        ],
    },
    "wallet_activity": {
        "description": "One row per wallet per day with sent and received volume.",
        "partition_field": "block_date",
        "partition_type": "DAY",
        "cluster_fields": ["wallet"],
        "columns": [
            ("block_date", "DATE", "UTC calendar day"),
            ("wallet", "STRING", "Wallet address"),
            ("transfer_count", "INT64", "Transfers involving the wallet"),
            ("total_volume", "FLOAT64", "Sent plus received volume"),
            ("sent_volume", "FLOAT64", "Volume sent"),
            ("received_volume", "FLOAT64", "Volume received"),
            ("_published_at", "TIMESTAMP", "When Analytic Sages published this row"),
        ],
    },
}


def fq_table(project: str, table: str, dataset: str = CURATED_DATASET) -> str:
    return f"{project}.{dataset}.{table}"


def create_table_ddl(project: str, table: str, dataset: str = CURATED_DATASET) -> str:
    spec = CURATED_TABLES[table]
    cols = ",\n  ".join(f"{name} {dtype}" for name, dtype, _ in spec["columns"])
    partition = spec["partition_field"]
    cluster = ", ".join(spec["cluster_fields"])
    partition_expr = (
        partition if partition == "block_date" else f"DATE({partition})"
    )
    return f"""CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (
  {cols}
)
PARTITION BY {partition_expr}
CLUSTER BY {cluster}
OPTIONS(
  description="{spec['description']}"
)"""


TOKEN_ACTIVITY_SQL = """
CREATE OR REPLACE TABLE `{project}.{dataset}.token_activity`
PARTITION BY block_date
CLUSTER BY mint
AS
SELECT
  DATE(block_timestamp) AS block_date,
  mint,
  COUNT(*) AS transfer_count,
  SUM(amount_ui) AS total_volume,
  COUNT(DISTINCT source) AS unique_senders,
  COUNT(DISTINCT destination) AS unique_receivers,
  CURRENT_TIMESTAMP() AS _published_at
FROM `{project}.{dataset}.token_transfers`
WHERE mint IS NOT NULL
GROUP BY 1, 2
"""

WALLET_ACTIVITY_SQL = """
CREATE OR REPLACE TABLE `{project}.{dataset}.wallet_activity`
PARTITION BY block_date
CLUSTER BY wallet
AS
WITH unified AS (
  SELECT DATE(block_timestamp) AS block_date, source AS wallet, amount_ui, 'sent' AS direction
  FROM `{project}.{dataset}.token_transfers`
  WHERE source IS NOT NULL
  UNION ALL
  SELECT DATE(block_timestamp) AS block_date, destination AS wallet, amount_ui, 'received' AS direction
  FROM `{project}.{dataset}.token_transfers`
  WHERE destination IS NOT NULL
)
SELECT
  block_date,
  wallet,
  COUNT(*) AS transfer_count,
  SUM(amount_ui) AS total_volume,
  SUM(IF(direction = 'sent', amount_ui, 0)) AS sent_volume,
  SUM(IF(direction = 'received', amount_ui, 0)) AS received_volume,
  CURRENT_TIMESTAMP() AS _published_at
FROM unified
GROUP BY 1, 2
"""
