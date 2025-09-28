"""CSV ingestion utilities for broker statements."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Callable, Dict, Iterable, List

from app.services.trades import TradeDTO


@dataclass
class CSVRowMapping:
    """Mapping of CSV column names."""

    date: str
    symbol: str
    side: str
    qty: str
    price: str
    fee: str
    tax: str
    order_id: str


Parser = Callable[[int, Iterable[dict[str, str]]], List[TradeDTO]]


def parse_generic_tw_rows(account_id: int, rows: Iterable[dict[str, str]]) -> List[TradeDTO]:
    """Parse rows for generic Taiwan CSV layout."""

    trades: List[TradeDTO] = []
    for row in rows:
        try:
            trade_dt = datetime.strptime(row["date"], "%Y-%m-%d")
            trades.append(
                TradeDTO(
                    account_id=account_id,
                    symbol=row["symbol"],
                    side=row["side"].upper(),
                    qty=float(row["qty"]),
                    price=float(row["price"]),
                    trade_ts=trade_dt,
                    order_id=row.get("order_id"),
                    fee=float(row.get("fee", 0) or 0),
                    tax=float(row.get("tax", 0) or 0),
                    venue=row.get("venue"),
                    raw=row,
                )
            )
        except (KeyError, ValueError):
            continue
    return trades


DIALECTS: Dict[str, Parser] = {
    "generic_tw": parse_generic_tw_rows,
}


def parse_generic_tw_csv(account_id: int, content: str) -> List[TradeDTO]:
    """Parse CSV content according to the generic Taiwan layout."""

    buffer = StringIO(content)
    reader = csv.DictReader(buffer)
    return parse_generic_tw_rows(account_id, reader)
