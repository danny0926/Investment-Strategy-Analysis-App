"""Mock IBKR ingestor leveraging Client Portal interface placeholders."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from app.models.models import Account
from app.services.trades import TradeDTO


def fetch_trades(account: Account, start: datetime, end: datetime) -> List[TradeDTO]:
    """Return simulated IBKR trades."""

    trades: List[TradeDTO] = []
    ts = start
    while ts <= end:
        trades.append(
            TradeDTO(
                account_id=account.id,
                symbol="AAPL",
                side="BUY" if ts.day % 2 == 0 else "SELL",
                qty=10,
                price=170.0,
                trade_ts=ts,
                order_id=f"IBKR-{ts.timestamp()}",
                fee=1.5,
                tax=0.0,
                venue="NASDAQ",
                raw={"source": "mock"},
            )
        )
        ts += timedelta(days=1)
    return trades


def fetch_positions(account: Account) -> list[dict]:
    """Return static IBKR positions."""

    return [
        {"symbol": "AAPL", "qty": 20, "avg_price": 150.0},
    ]
