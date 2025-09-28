"""Mock Shioaji broker ingestor."""
from __future__ import annotations

from datetime import datetime, timedelta
from random import random
from typing import List

from app.models.models import Account
from app.services.trades import TradeDTO


def fetch_trades(account: Account, start: datetime, end: datetime) -> List[TradeDTO]:
    """Return mock trades for Shioaji connection."""

    trades: List[TradeDTO] = []
    ts = start
    while ts <= end:
        trades.append(
            TradeDTO(
                account_id=account.id,
                symbol="2330.TW",
                side="BUY" if random() > 0.5 else "SELL",
                qty=1,
                price=600 + random() * 5,
                trade_ts=ts,
                order_id=f"SJ-{ts.timestamp()}",
                fee=5,
                tax=2,
                venue="TWSE",
                raw={"source": "mock"},
            )
        )
        ts += timedelta(days=1)
    return trades


def fetch_positions(account: Account) -> list[dict]:
    """Return mock positions."""

    return [
        {"symbol": "2330.TW", "qty": 5, "avg_price": 590.0},
    ]
