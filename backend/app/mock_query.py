"""Shape-aware mock query results for the learning sandbox."""

from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.query_policy import QueryPolicy

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SOL = "So11111111111111111111111111111111111111112"


def _hourly_timestamps(hours: int = 48) -> list[str]:
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=hours - 1)
    return [(start + timedelta(hours=i)).isoformat() for i in range(hours)]


def _payload(columns: list[str], data: list[dict[str, Any]], policy: QueryPolicy, sql: str) -> dict:
    start, end = policy.window()
    return {
        "columns": columns,
        "data": data,
        "row_count": len(data),
        "bytes_processed": 12345,
        "bytes_billed": 0,
        "job_id": "mock-learning-job",
        "cache_hit": True,
        "policy": policy.to_public_dict(),
        "mode": "mock",
        "sql": sql,
        "note": f"Mock learning result for window {start} to {end}",
    }


def mock_for_sql(sql: str, policy: QueryPolicy) -> dict[str, Any] | None:
    s = sql.lower()

    if "peak_hour_volume" in s or "max(hourly_volume" in s:
        hours = _hourly_timestamps(48)
        peak = max(
            180_000 + 40_000 * math.sin(i / 4) + (i % 5) * 8_000 for i in range(len(hours))
        )
        return _payload(["peak_hour_volume"], [{"peak_hour_volume": round(peak, 2)}], policy, sql)

    if "solana_curated.transfers" in s and "timestamp_trunc" in s and "transfer_volume" in s:
        data = [
            {"hour": h, "transfer_volume": round(120_000 + 35_000 * math.sin(i / 3) + (i % 4) * 5_000, 2)}
            for i, h in enumerate(_hourly_timestamps(48))
        ]
        return _payload(["hour", "transfer_volume"], data, policy, sql)

    if "solana_curated.transfers" in s and "timestamp_trunc" in s and "transfer_count" in s:
        data = [
            {"hour": h, "transfer_count": int(900 + 180 * math.sin(i / 2.5) + (i % 3) * 40)}
            for i, h in enumerate(_hourly_timestamps(48))
        ]
        return _payload(["hour", "transfer_count"], data, policy, sql)

    if "solana_curated.transfers" in s and "group by mint" in s:
        tokens = [
            (USDC, 2_450_000),
            (SOL, 1_820_000),
            ("DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", 640_000),
            ("7dHbWXmci3dT8RDYWJYWPDP5Z7F7KqJqZqZqZqZqZqZqZ", 310_000),
            ("JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN", 275_000),
        ]
        data = [{"mint": mint, "total_volume": vol} for mint, vol in tokens]
        return _payload(["mint", "total_volume"], data, policy, sql)

    if "solana_curated.transactions" in s and "timestamp_trunc" in s:
        data = [
            {"hour": h, "tx_count": int(4_200 + 900 * math.sin(i / 3.5) + (i % 6) * 120)}
            for i, h in enumerate(_hourly_timestamps(48))
        ]
        return _payload(["hour", "tx_count"], data, policy, sql)

    if "solana_curated.token_activity" in s:
        start, end = policy.window()
        days = (end - start).days + 1
        data: list[dict[str, Any]] = []
        for d in range(days):
            day = (start + timedelta(days=d)).isoformat()
            data.append(
                {
                    "block_date": day,
                    "mint": USDC,
                    "transfer_count": 12000 - d * 300,
                    "total_volume": 4_500_000.0 - d * 50_000,
                }
            )
        cols = list(data[0].keys()) if data else ["block_date", "mint", "transfer_count", "total_volume"]
        return _payload(cols, data[: policy.max_rows], policy, sql)

    if "solana_curated.wallet_activity" in s:
        start, end = policy.window()
        data = [
            {
                "wallet": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
                "received_volume": 12500.0 - i * 200,
            }
            for i in range(min(10, policy.max_rows))
        ]
        return _payload(["wallet", "received_volume"], data, policy, sql)

    # Generic transfers fallback (labs starter SQL)
    if "solana_curated.transfers" in s:
        end = policy.window()[1]
        data = [
            {
                "mint": USDC,
                "sender": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
                "receiver": "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
                "amount": 1000.0 - i * 10,
                "block_timestamp": f"{end.isoformat()}T12:00:00+00:00",
            }
            for i in range(min(10, policy.max_rows))
        ]
        return _payload(
            ["mint", "sender", "receiver", "amount", "block_timestamp"],
            data,
            policy,
            sql,
        )

    return None
