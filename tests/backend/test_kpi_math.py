"""Unit tests for KPI utilities."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from dataclasses import dataclass

from app.services.trades import compute_kpis, equity_curve, max_drawdown, profit_factor


@dataclass
class DummyTrade:
    """Simple stand-in for the Trade ORM model."""

    side: str
    qty: float
    price: float
    fee: float = 0
    tax: float = 0
    trade_ts: datetime = datetime(2024, 1, 1, tzinfo=timezone.utc)


def make_trade(side: str, qty: float, price: float, fee: float = 0, tax: float = 0) -> DummyTrade:
    return DummyTrade(side=side, qty=qty, price=price, fee=fee, tax=tax)


def test_profit_factor_zero_losses() -> None:
    assert profit_factor(100, 0) is None


def test_profit_factor_basic() -> None:
    assert pytest.approx(profit_factor(200, -100), rel=1e-3) == 2.0


def test_equity_curve_empty() -> None:
    assert equity_curve([]).empty


def test_equity_curve_basic() -> None:
    trades = [make_trade("SELL", 1, 10), make_trade("BUY", 1, 9)]
    series = equity_curve(trades)
    assert series.iloc[-1] != 0


def test_max_drawdown_empty() -> None:
    value, peak, trough = max_drawdown(pd.Series(dtype=float))
    assert value == 0
    assert peak is None
    assert trough is None


def test_max_drawdown_basic() -> None:
    series = pd.Series([100, 110, 90, 95], index=pd.date_range("2024-01-01", periods=4))
    value, peak, trough = max_drawdown(series)
    assert value == -20
    assert peak is not None
    assert trough is not None


def test_compute_kpis_single_trade() -> None:
    trade = make_trade("SELL", 1, 100)
    kpis = compute_kpis([trade])
    assert kpis["total_trades"] == 1
    assert kpis["expectancy"] == pytest.approx(100)


def test_compute_kpis_losses() -> None:
    trade = make_trade("BUY", 1, 100)
    kpis = compute_kpis([trade])
    assert kpis["avg_loss"] < 0


def test_compute_kpis_mixed() -> None:
    trades = [make_trade("SELL", 1, 120), make_trade("BUY", 1, 80)]
    kpis = compute_kpis(trades)
    assert kpis["win_rate"] == 0.5
    assert kpis["total_trades"] == 2

