"""Offline mock rows so the portal works without Trino."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any


def _days_ago(n: int) -> date:
    return date.today() - timedelta(days=n)


MOCK_TOKEN_ACTIVITY: list[dict[str, Any]] = [
    {
        "block_date": _days_ago(i),
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "transfer_count": 12000 - i * 300,
        "total_volume": 4_500_000.0 - i * 50_000,
        "unique_senders": 3200 - i * 20,
        "unique_receivers": 4100 - i * 25,
    }
    for i in range(7)
] + [
    {
        "block_date": _days_ago(i),
        "mint": "So11111111111111111111111111111111111111112",
        "transfer_count": 8000 - i * 200,
        "total_volume": 2_100_000.0 - i * 30_000,
        "unique_senders": 2100 - i * 15,
        "unique_receivers": 2500 - i * 18,
    }
    for i in range(7)
]

MOCK_WALLET_ACTIVITY: list[dict[str, Any]] = [
    {
        "block_date": _days_ago(i),
        "wallet": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
        "transfer_count": 40 - i,
        "total_volume": 12500.0 - i * 200,
        "sent_volume": 7000.0 - i * 100,
        "received_volume": 5500.0 - i * 100,
    }
    for i in range(5)
]

MOCK_TRANSFERS: list[dict[str, Any]] = [
    {
        "block_slot": 280_000_000 - i,
        "block_timestamp": datetime.now(timezone.utc) - timedelta(minutes=i * 12),
        "tx_signature": f"MockSig{'A' * 40}{i}",
        "source": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
        "destination": "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK",
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "value": 1_000_000 * (i + 1),
        "decimals": 6,
        "fee": 5000,
        "memo": None,
        "transfer_type": "transfer",
    }
    for i in range(10)
]

MOCK_TOKENS: list[dict[str, Any]] = [
    {
        "mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "name": "USD Coin",
        "symbol": "USDC",
        "decimals": 6,
        "is_nft": False,
    },
    {
        "mint": "So11111111111111111111111111111111111111112",
        "name": "Wrapped SOL",
        "symbol": "SOL",
        "decimals": 9,
        "is_nft": False,
    },
]


def filter_by_date(
    rows: list[dict[str, Any]],
    date_field: str,
    start_date: date | None,
    end_date: date | None,
) -> list[dict[str, Any]]:
    if start_date is None or end_date is None:
        return rows

    def as_date(value: Any) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        return date.fromisoformat(str(value)[:10])

    return [r for r in rows if start_date <= as_date(r[date_field]) <= end_date]
