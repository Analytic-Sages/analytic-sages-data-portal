"""Learner-facing curated dataset catalog (Phase 1 tables)."""

from __future__ import annotations

from typing import Any

from app.bigquery_links import curated_table_id, bigquery_table_url


def _transfers_sql() -> str:
    t = curated_table_id("transfers")
    return (
        f"SELECT\n"
        f"  mint,\n"
        f"  source AS sender,\n"
        f"  destination AS receiver,\n"
        f"  amount_ui AS amount,\n"
        f"  block_timestamp\n"
        f"FROM {t}\n"
        f"WHERE DATE(block_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)\n"
        f"  AND CURRENT_DATE()\n"
        f"ORDER BY amount_ui DESC\n"
        f"LIMIT 10"
    )


LAB_01: dict[str, Any] = {
    "id": "lab-01-explore-transfers",
    "slug": "lab-01-explore-transfers",
    "number": 1,
    "title": "Explore Token Transfers",
    "level": "beginner",
    "dataset_slug": "transfers",
    "status": "available",
    "estimated_minutes": 15,
    "skills": ["SELECT", "WHERE", "ORDER BY", "LIMIT"],
    "objective": (
        "Understand how token transfers are represented in Analytic Sages "
        "curated Solana data."
    ),
    "task": (
        "Find the largest token transfers and learn how transfer data is structured."
    ),
    "starter_sql": _transfers_sql(),
    "check_hint": (
        "Your result should return 10 rows, ordered by amount from largest to smallest."
    ),
    "what_you_learn": [
        "How transfer events are stored as rows",
        "How to rank transfers by amount",
        "How to read sender, receiver, mint, and amount columns",
    ],
}


def _token_activity_sql() -> str:
    t = curated_table_id("token_activity")
    return (
        f"SELECT\n"
        f"  mint,\n"
        f"  SUM(transfer_count) AS transfers,\n"
        f"  SUM(total_volume) AS volume\n"
        f"FROM {t}\n"
        f"WHERE block_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)\n"
        f"  AND CURRENT_DATE()\n"
        f"GROUP BY mint\n"
        f"ORDER BY transfers DESC\n"
        f"LIMIT 10"
    )


def _wallet_activity_sql() -> str:
    t = curated_table_id("wallet_activity")
    return (
        f"SELECT\n"
        f"  wallet,\n"
        f"  SUM(sent_volume) AS sent,\n"
        f"  SUM(received_volume) AS received\n"
        f"FROM {t}\n"
        f"WHERE block_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)\n"
        f"  AND CURRENT_DATE()\n"
        f"GROUP BY wallet\n"
        f"ORDER BY received DESC\n"
        f"LIMIT 10"
    )


LAB_02: dict[str, Any] = {
    "id": "lab-02-active-tokens",
    "slug": "lab-02-active-tokens",
    "number": 2,
    "title": "Find the Most Active Tokens",
    "level": "beginner",
    "dataset_slug": "token_activity",
    "status": "available",
    "estimated_minutes": 20,
    "skills": ["GROUP BY", "SUM", "ORDER BY"],
    "objective": (
        "Learn to aggregate daily token activity and identify which tokens "
        "drive the most transfer volume."
    ),
    "task": "Identify which tokens generate the most transfer activity.",
    "starter_sql": _token_activity_sql(),
    "check_hint": (
        "Your result should list tokens ranked by total transfer count, with volume included."
    ),
    "what_you_learn": [
        "How daily token rollups work",
        "How to aggregate with GROUP BY and SUM",
        "How to compare tokens by activity",
    ],
}


LAB_03: dict[str, Any] = {
    "id": "lab-03-wallet-activity",
    "slug": "lab-03-wallet-activity",
    "number": 3,
    "title": "Analyze Wallet Activity",
    "level": "beginner",
    "dataset_slug": "wallet_activity",
    "status": "available",
    "estimated_minutes": 20,
    "skills": ["GROUP BY", "SUM", "ORDER BY"],
    "objective": (
        "Compare wallets by sent and received volume using curated wallet activity."
    ),
    "task": "Compare wallets by sent and received volume.",
    "starter_sql": _wallet_activity_sql(),
    "check_hint": (
        "Your result should show wallets ordered by received volume, with sent volume included."
    ),
    "what_you_learn": [
        "How wallet-level daily activity is stored",
        "How to separate sent vs received volume",
        "How to rank wallets for analysis",
    ],
}


LAB_04: dict[str, Any] = {
    "id": "lab-04-high-volume-wallets",
    "slug": "lab-04-high-volume-wallets",
    "number": 4,
    "title": "Identify High-Volume Wallets",
    "level": "intermediate",
    "dataset_slug": "wallet_activity",
    "status": "coming_soon",
    "estimated_minutes": 25,
    "skills": ["FILTER", "HAVING", "JOIN ideas"],
    "objective": "Find wallets with unusually high transfer volume.",
    "task": "Identify wallets with the highest total volume in the learning window.",
    "starter_sql": "",
    "check_hint": "Coming soon.",
    "what_you_learn": [
        "Filtering aggregated results",
        "Comparing wallet behavior",
    ],
}


LAB_05: dict[str, Any] = {
    "id": "lab-05-compare-token-activity",
    "slug": "lab-05-compare-token-activity",
    "number": 5,
    "title": "Compare Token Activity",
    "level": "intermediate",
    "dataset_slug": "token_activity",
    "status": "coming_soon",
    "estimated_minutes": 25,
    "skills": ["CASE", "ratios"],
    "objective": "Compare multiple tokens over the same time window.",
    "task": "Build a comparison of transfer counts across top tokens.",
    "starter_sql": "",
    "check_hint": "Coming soon.",
    "what_you_learn": [
        "Side-by-side token comparison",
        "Choosing useful metrics",
    ],
}


LAB_06: dict[str, Any] = {
    "id": "lab-06-daily-network-activity",
    "slug": "lab-06-daily-network-activity",
    "number": 6,
    "title": "Analyze Daily Network Activity",
    "level": "intermediate",
    "dataset_slug": "transactions",
    "status": "coming_soon",
    "estimated_minutes": 30,
    "skills": ["TIME SERIES", "COUNT"],
    "objective": "Measure network activity using transaction counts.",
    "task": "Summarize transaction activity across the learning window.",
    "starter_sql": "",
    "check_hint": "Coming soon.",
    "what_you_learn": [
        "Transaction-level analysis",
        "Building time series summaries",
    ],
}


LAB_07: dict[str, Any] = {
    "id": "lab-07-unusual-transfers",
    "slug": "lab-07-unusual-transfers",
    "number": 7,
    "title": "Detect Unusual Transfer Activity",
    "level": "advanced",
    "dataset_slug": "transfers",
    "status": "coming_soon",
    "estimated_minutes": 40,
    "skills": ["OUTLIERS", "THRESHOLDS"],
    "objective": "Spot unusually large transfers in curated transfer data.",
    "task": "Design a query that surfaces unusual transfer amounts.",
    "starter_sql": "",
    "check_hint": "Coming soon.",
    "what_you_learn": [
        "Defining what unusual means",
        "Independent problem solving",
    ],
}


LAB_08: dict[str, Any] = {
    "id": "lab-08-token-intelligence",
    "slug": "lab-08-token-intelligence",
    "number": 8,
    "title": "Build a Token Intelligence Dashboard",
    "level": "advanced",
    "dataset_slug": "token_activity",
    "status": "coming_soon",
    "estimated_minutes": 45,
    "skills": ["VISUALIZE", "DASHBOARD"],
    "objective": "Combine queries and charts into a token intelligence board.",
    "task": "Plan and build a multi-chart dashboard from token activity.",
    "starter_sql": "",
    "check_hint": "Coming soon.",
    "what_you_learn": [
        "Turning analysis into a dashboard",
        "Choosing chart types for stakeholders",
    ],
}


ALL_LABS: list[dict[str, Any]] = [
    LAB_01,
    LAB_02,
    LAB_03,
    LAB_04,
    LAB_05,
    LAB_06,
    LAB_07,
    LAB_08,
]


DATASETS: list[dict[str, Any]] = [
    {
        "id": "transfers",
        "name": "Solana Transfers",
        "slug": "transfers",
        "description": (
            "Token transfer events curated by Analytic Sages. Each row is one "
            "transfer between wallets for a given token."
        ),
        "what_you_learn": (
            "Practice filtering, sorting, and aggregating real token transfer activity."
        ),
        "grain": "One row per token transfer",
        "category": "solana",
        "status": "available",
        "curated_table": curated_table_id("transfers"),
        "open_in_bigquery_url": bigquery_table_url("transfers"),
        "freshness": "Published by Analytic Sages curated pipeline",
        "coverage": "Solana mainnet token transfers in the published date range",
        "related_datasets": ["token_activity", "wallet_activity", "transactions"],
        "internal_table_key": "transfers",
        "columns": [
            {"name": "block_slot", "type": "INT64", "description": "Solana slot"},
            {
                "name": "block_timestamp",
                "type": "TIMESTAMP",
                "description": "Block time (UTC)",
            },
            {
                "name": "tx_signature",
                "type": "STRING",
                "description": "Transaction signature",
            },
            {"name": "source", "type": "STRING", "description": "Sender wallet"},
            {
                "name": "destination",
                "type": "STRING",
                "description": "Receiver wallet",
            },
            {"name": "mint", "type": "STRING", "description": "Token mint address"},
            {
                "name": "amount",
                "type": "NUMERIC",
                "description": "Transfer amount (raw units)",
            },
            {"name": "decimals", "type": "INT64", "description": "Token decimals"},
            {
                "name": "amount_ui",
                "type": "FLOAT64",
                "description": "Human-readable amount",
            },
            {"name": "fee", "type": "NUMERIC", "description": "Transfer fee if any"},
            {"name": "memo", "type": "STRING", "description": "Optional memo"},
            {
                "name": "transfer_type",
                "type": "STRING",
                "description": "Transfer type",
            },
        ],
        "example_question": "What were the largest token transfers recently?",
        "sql_examples": [
            {
                "title": "Top 10 transfers by amount",
                "sql": _transfers_sql(),
            }
        ],
        "labs": [
            {
                "id": LAB_01["id"],
                "title": LAB_01["title"],
                "level": LAB_01["level"],
                "prompt": LAB_01["task"],
                "slug": LAB_01["slug"],
            }
        ],
        "projects": [
            {
                "id": "proj-transfer-dashboard",
                "title": "Token transfer dashboard",
                "level": "intermediate",
                "prompt": (
                    "Build a dashboard of daily transfer count and volume for "
                    "USDC and SOL using Analytic Sages curated tables."
                ),
            }
        ],
    },
    {
        "id": "token_activity",
        "name": "Solana Token Activity",
        "slug": "token_activity",
        "description": (
            "Daily activity for each Solana token: transfer counts, volume, and "
            "unique wallets."
        ),
        "what_you_learn": (
            "Compare tokens over time and find which ones were most active."
        ),
        "grain": "One row per token per day",
        "category": "solana",
        "status": "available",
        "curated_table": curated_table_id("token_activity"),
        "open_in_bigquery_url": bigquery_table_url("token_activity"),
        "freshness": "Rebuilt from curated transfers on each publish",
        "coverage": "Daily rollups from published transfers",
        "related_datasets": ["transfers", "wallet_activity"],
        "internal_table_key": "token_activity",
        "columns": [
            {"name": "block_date", "type": "DATE", "description": "UTC calendar day"},
            {"name": "mint", "type": "STRING", "description": "Token mint address"},
            {
                "name": "transfer_count",
                "type": "INT64",
                "description": "Number of transfers that day",
            },
            {
                "name": "total_volume",
                "type": "FLOAT64",
                "description": "Sum of amount_ui that day",
            },
            {
                "name": "unique_senders",
                "type": "INT64",
                "description": "Distinct sending wallets",
            },
            {
                "name": "unique_receivers",
                "type": "INT64",
                "description": "Distinct receiving wallets",
            },
        ],
        "example_question": "Which tokens had the highest transfer activity last week?",
        "sql_examples": [
            {
                "title": "Top tokens by transfer count",
                "sql": (
                    f"SELECT mint, SUM(transfer_count) AS transfers\n"
                    f"FROM {curated_table_id('token_activity')}\n"
                    f"WHERE block_date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)\n"
                    f"  AND CURRENT_DATE()\n"
                    f"GROUP BY mint\n"
                    f"ORDER BY transfers DESC\n"
                    f"LIMIT 20"
                ),
            }
        ],
        "labs": [
            {
                "id": LAB_02["id"],
                "title": LAB_02["title"],
                "level": LAB_02["level"],
                "prompt": LAB_02["task"],
                "slug": LAB_02["slug"],
            }
        ],
        "projects": [],
    },
    {
        "id": "wallet_activity",
        "name": "Solana Wallet Activity",
        "slug": "wallet_activity",
        "description": (
            "Daily activity for each wallet, including how much was sent and received."
        ),
        "what_you_learn": "Study wallet behavior and sent versus received volume.",
        "grain": "One row per wallet per day",
        "category": "solana",
        "status": "available",
        "curated_table": curated_table_id("wallet_activity"),
        "open_in_bigquery_url": bigquery_table_url("wallet_activity"),
        "freshness": "Rebuilt from curated transfers on each publish",
        "coverage": "Daily rollups from published transfers",
        "related_datasets": ["transfers", "token_activity"],
        "internal_table_key": "wallet_activity",
        "columns": [
            {"name": "block_date", "type": "DATE", "description": "UTC calendar day"},
            {"name": "wallet", "type": "STRING", "description": "Wallet address"},
            {
                "name": "transfer_count",
                "type": "INT64",
                "description": "Transfers involving the wallet",
            },
            {
                "name": "total_volume",
                "type": "FLOAT64",
                "description": "Sent plus received volume",
            },
            {
                "name": "sent_volume",
                "type": "FLOAT64",
                "description": "Volume sent",
            },
            {
                "name": "received_volume",
                "type": "FLOAT64",
                "description": "Volume received",
            },
        ],
        "example_question": "Which wallets received the most volume yesterday?",
        "sql_examples": [
            {
                "title": "Top receivers by volume",
                "sql": (
                    f"SELECT wallet, SUM(received_volume) AS received\n"
                    f"FROM {curated_table_id('wallet_activity')}\n"
                    f"WHERE block_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)\n"
                    f"GROUP BY wallet\n"
                    f"ORDER BY received DESC\n"
                    f"LIMIT 25"
                ),
            }
        ],
        "labs": [
            {
                "id": LAB_03["id"],
                "title": LAB_03["title"],
                "level": LAB_03["level"],
                "prompt": LAB_03["task"],
                "slug": LAB_03["slug"],
            }
        ],
        "projects": [],
    },
    {
        "id": "transactions",
        "name": "Solana Transactions",
        "slug": "transactions",
        "description": (
            "Solana transactions curated for learning transaction-level analysis."
        ),
        "what_you_learn": (
            "Explore fees, status, and compute usage across transactions."
        ),
        "grain": "One row per transaction",
        "category": "solana",
        "status": "available",
        "curated_table": curated_table_id("transactions"),
        "open_in_bigquery_url": bigquery_table_url("transactions"),
        "freshness": "Published by Analytic Sages curated pipeline",
        "coverage": "Solana mainnet transactions in the published date range",
        "related_datasets": ["transfers"],
        "internal_table_key": None,
        "columns": [
            {"name": "block_slot", "type": "INT64", "description": "Solana slot"},
            {
                "name": "block_timestamp",
                "type": "TIMESTAMP",
                "description": "Block time (UTC)",
            },
            {
                "name": "signature",
                "type": "STRING",
                "description": "Transaction signature",
            },
            {
                "name": "tx_index",
                "type": "INT64",
                "description": "Index within the block",
            },
            {"name": "fee", "type": "NUMERIC", "description": "Fee paid (lamports)"},
            {
                "name": "status",
                "type": "STRING",
                "description": "success or failure",
            },
            {"name": "err", "type": "STRING", "description": "Error message if failed"},
            {
                "name": "compute_units_consumed",
                "type": "NUMERIC",
                "description": "Compute units used",
            },
        ],
        "example_question": "What share of recent transactions failed?",
        "sql_examples": [
            {
                "title": "Success vs failure counts",
                "sql": (
                    f"SELECT status, COUNT(*) AS tx_count\n"
                    f"FROM {curated_table_id('transactions')}\n"
                    f"GROUP BY status\n"
                    f"ORDER BY tx_count DESC"
                ),
            }
        ],
        "labs": [],
        "projects": [],
    },
]


def list_datasets() -> list[dict[str, Any]]:
    return [
        {
            "id": d["id"],
            "name": d["name"],
            "slug": d["slug"],
            "description": d["description"],
            "grain": d["grain"],
            "category": d["category"],
            "status": d["status"],
            "curated_table": d["curated_table"],
            "open_in_bigquery_url": d["open_in_bigquery_url"],
            "freshness": d.get("freshness"),
            "example_question": d["example_question"],
            "column_count": len(d["columns"]),
        }
        for d in DATASETS
    ]


def get_dataset(slug: str) -> dict[str, Any] | None:
    for dataset in DATASETS:
        if dataset["slug"] == slug or dataset["id"] == slug:
            return dataset
    return None


def get_lab(slug: str) -> dict[str, Any] | None:
    needle = (slug or "").strip().lower()
    for item in ALL_LABS:
        aliases = {item["id"], item["slug"], f"lab-{item['number']:02d}"}
        if needle in {a.lower() for a in aliases}:
            lab = dict(item)
            lab["curated_table"] = curated_table_id(lab["dataset_slug"])
            return lab
    return None


def list_labs() -> list[dict[str, Any]]:
    return [get_lab(item["slug"]) for item in ALL_LABS if get_lab(item["slug"])]
