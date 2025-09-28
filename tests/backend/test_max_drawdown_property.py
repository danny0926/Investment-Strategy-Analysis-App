"""Property-style tests for max drawdown stability."""
from __future__ import annotations

import random

import pandas as pd

from app.services.trades import max_drawdown


def test_max_drawdown_never_positive() -> None:
    values = pd.Series([random.uniform(90, 110) for _ in range(50)])
    drawdown, _, _ = max_drawdown(values)
    assert drawdown <= 0


def test_max_drawdown_peak_before_trough() -> None:
    values = pd.Series([100, 120, 110, 130, 90], index=pd.date_range("2024-01-01", periods=5))
    drawdown, peak, trough = max_drawdown(values)
    assert peak <= trough
