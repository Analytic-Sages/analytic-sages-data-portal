"""
Typed schemas for Solana tables. Matches actual bigquery-public-data.crypto_solana_mainnet_us
schemas as verified from BQ console. Used to enforce column mapping and detect drift.
"""
from pyspark.sql.types import (
    StructType, StructField, LongType, StringType, TimestampType,
    DateType, ArrayType, BooleanType, IntegerType, DecimalType
)

# Token transfers - actual BQ schema has block_slot, not slot, and value/decimals as NUMERIC
TOKEN_TRANSFERS_SCHEMA = StructType([
    StructField("block_slot", LongType(), True),
    StructField("block_hash", StringType(), True),
    StructField("block_timestamp", TimestampType(), True),
    StructField("tx_signature", StringType(), True),
    StructField("source", StringType(), True),
    StructField("destination", StringType(), True),
    StructField("authority", StringType(), True),
    StructField("value", DecimalType(38, 9), True),          # BQ NUMERIC
    StructField("decimals", DecimalType(38, 9), True),        # BQ NUMERIC
    StructField("mint", StringType(), True),
    StructField("mint_authority", StringType(), True),
    StructField("fee", DecimalType(38, 9), True),
    StructField("fee_decimals", DecimalType(38, 9), True),
    StructField("memo", StringType(), True),
    StructField("transfer_type", StringType(), True),
    StructField("_ingested_at", TimestampType(), True),
])

# Tokens - metadata table
TOKENS_SCHEMA = StructType([
    StructField("block_slot", LongType(), True),
    StructField("block_hash", StringType(), True),
    StructField("block_timestamp", TimestampType(), True),
    StructField("tx_signature", StringType(), True),
    StructField("retrieval_timestamp", TimestampType(), True),
    StructField("is_nft", BooleanType(), True),
    StructField("mint", StringType(), True),
    StructField("update_authority", StringType(), True),
    StructField("name", StringType(), True),
    StructField("symbol", StringType(), True),
    StructField("uri", StringType(), True),
    StructField("seller_fee_basis_points", DecimalType(38, 9), True),
    StructField("creators", ArrayType(StructType([
        StructField("address", StringType(), True),
        StructField("share", LongType(), True),
        StructField("verified", BooleanType(), True),
    ])), True),
    StructField("primary_sale_happened", BooleanType(), True),
    StructField("is_mutable", BooleanType(), True),
    StructField("_ingested_at", TimestampType(), True),
])

# Transactions - heavy table, actual BQ uses block_slot + index + signature
TRANSACTIONS_SCHEMA = StructType([
    StructField("block_slot", LongType(), True),
    StructField("block_hash", StringType(), True),
    StructField("block_timestamp", TimestampType(), True),
    StructField("recent_block_hash", StringType(), True),
    StructField("signature", StringType(), True),
    StructField("index", LongType(), True),
    StructField("fee", DecimalType(38, 9), True),
    StructField("status", StringType(), True),
    StructField("err", StringType(), True),
    StructField("compute_units_consumed", DecimalType(38, 9), True),
    StructField("accounts", ArrayType(StructType([
        StructField("account", StringType(), True),
        StructField("is_signer", BooleanType(), True),
        StructField("is_writable", BooleanType(), True),
    ])), True),
    StructField("log_messages", ArrayType(StringType()), True),
    StructField("balance_changes", ArrayType(StructType([
        StructField("account", StringType(), True),
        StructField("pre_balance", DecimalType(38, 9), True),
        StructField("post_balance", DecimalType(38, 9), True),
    ])), True),
    StructField("pre_token_balances", ArrayType(StructType([
        StructField("account", StringType(), True),
        StructField("mint", StringType(), True),
        StructField("amount", StringType(), True),
    ])), True),
    StructField("post_token_balances", ArrayType(StructType([
        StructField("account", StringType(), True),
        StructField("mint", StringType(), True),
        StructField("amount", StringType(), True),
    ])), True),
    StructField("_ingested_at", TimestampType(), True),
])

# Blocks - keep generic, actual BQ Blocks table mirrors block_slot pattern
BLOCKS_SCHEMA = StructType([
    StructField("block_slot", LongType(), True),
    StructField("block_hash", StringType(), True),
    StructField("block_timestamp", TimestampType(), True),
    StructField("previous_block_hash", StringType(), True),
    StructField("parent_slot", LongType(), True),
    StructField("_ingested_at", TimestampType(), True),
])

TABLE_SCHEMAS = {
    "blocks": BLOCKS_SCHEMA,
    "transactions": TRANSACTIONS_SCHEMA,
    "token_transfers": TOKEN_TRANSFERS_SCHEMA,
    "tokens": TOKENS_SCHEMA,
    # legacy aliases
    "transfers": TOKEN_TRANSFERS_SCHEMA,
}

# Merge keys - natural PKs from actual BQ schemas
MERGE_KEYS = {
    "blocks": ["block_slot"],
    "transactions": ["block_slot", "index"],  # signature is unique but slot+index is the partitioned key
    "token_transfers": ["block_slot", "tx_signature", "source", "destination", "mint"],
    "tokens": ["mint"],
    "transfers": ["block_slot", "tx_signature", "source", "destination", "mint"],
}

PARTITION_COL = {
    "blocks": "block_timestamp",
    "transactions": "block_timestamp",
    "token_transfers": "block_timestamp",
    "tokens": None,
    "transfers": "block_timestamp",
}
