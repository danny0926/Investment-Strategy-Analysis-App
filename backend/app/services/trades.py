"""Trade service logic including KPI calculations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Sequence

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.models import Account, EquityDaily, KPI, Strategy, Trade, TradeTag

logger = get_logger(__name__)


@dataclass
class TradeDTO:
    """Simple data transfer object for trade ingestion."""

    account_id: int
    symbol: str
    side: str
    qty: float
    price: float
    trade_ts: datetime
    order_id: str | None = None
    fee: float = 0
    tax: float = 0
    venue: str | None = None
    raw: dict | None = None


def upsert_trades(db: Session, trades: Sequence[TradeDTO]) -> int:
    """Insert trades if they do not already exist."""

    if not trades:
        return 0
    from app.models.models import Symbol  # local import to avoid circular

    imported = 0
    for dto in trades:
        symbol = db.scalar(select(Symbol).where(Symbol.ticker == dto.symbol))
        if symbol is None:
            symbol = Symbol(ticker=dto.symbol, exchange="TWSE", asset_class="stock", lot_size=1000)
            db.add(symbol)
            db.flush()
        existing = db.scalar(
            select(Trade).where(
                Trade.account_id == dto.account_id,
                Trade.order_id == dto.order_id,
                Trade.trade_ts == dto.trade_ts,
                Trade.price == dto.price,
                Trade.qty == dto.qty,
            )
        )
        if existing:
            continue
        trade = Trade(
            account_id=dto.account_id,
            symbol_id=symbol.id,
            side=dto.side,
            qty=dto.qty,
            price=dto.price,
            trade_ts=dto.trade_ts,
            order_id=dto.order_id,
            fee=dto.fee,
            tax=dto.tax,
            venue=dto.venue,
            raw_json=dto.raw,
        )
        db.add(trade)
        imported += 1
    db.commit()
    return imported


def equity_curve(trades: Iterable[Trade]) -> pd.Series:
    """Return equity curve cumulative net PnL per day."""

    rows: list[tuple[date, float]] = []
    for trade in trades:
        pnl = float(trade.price) * float(trade.qty)
        pnl = pnl if trade.side == "SELL" else -pnl
        pnl -= float(trade.fee or 0) + float(trade.tax or 0)
        rows.append((trade.trade_ts.date(), pnl))
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame(rows, columns=["date", "pnl"])
    daily = df.groupby("date")["pnl"].sum().cumsum()
    daily.index = pd.to_datetime(daily.index)
    return daily


def max_drawdown(series: pd.Series) -> tuple[float, date | None, date | None]:
    """Calculate maximum drawdown of an equity curve."""

    if series.empty:
        return 0.0, None, None
    running_max = series.cummax()
    drawdowns = series - running_max
    mdd = drawdowns.min()
    trough_ts = drawdowns.idxmin()
    peak_ts = series.loc[:trough_ts].idxmax()
    try:
        peak_date = pd.Timestamp(peak_ts).date()
    except Exception:  # pragma: no cover - defensive
        peak_date = None
    try:
        trough_date = pd.Timestamp(trough_ts).date()
    except Exception:  # pragma: no cover - defensive
        trough_date = None
    return float(mdd), peak_date, trough_date


def profit_factor(win_sum: float, loss_sum: float) -> float | None:
    """Compute profit factor safely."""

    if loss_sum >= 0:
        return None
    if win_sum == 0:
        return 0.0
    return win_sum / abs(loss_sum)


def compute_kpis(trades: Sequence[Trade]) -> dict[str, float | None]:
    """Compute KPI metrics for a set of trades."""

    if not trades:
        return {
            "win_rate": None,
            "avg_win": None,
            "avg_loss": None,
            "profit_factor": None,
            "expectancy": None,
            "mdd": None,
            "total_trades": 0,
        }
    wins: list[float] = []
    losses: list[float] = []
    total_net = 0.0
    for trade in trades:
        pnl = float(trade.price) * float(trade.qty)
        pnl = pnl if trade.side == "SELL" else -pnl
        pnl -= float(trade.fee or 0) + float(trade.tax or 0)
        total_net += pnl
        if pnl > 0:
            wins.append(pnl)
        else:
            losses.append(pnl)
    win_rate = len(wins) / len(trades) if trades else None
    avg_win = sum(wins) / len(wins) if wins else None
    avg_loss = sum(losses) / len(losses) if losses else None
    pf = profit_factor(sum(wins), sum(losses) if losses else 0)
    expectancy = total_net / len(trades)
    equity = equity_curve(trades)
    mdd, _, _ = max_drawdown(equity)
    return {
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": pf,
        "expectancy": expectancy,
        "mdd": mdd,
        "total_trades": len(trades),
    }


def upsert_kpi(
    db: Session,
    scope: str,
    scope_ref_id: int,
    period_start: datetime,
    period_end: datetime,
    trades: Sequence[Trade],
) -> KPI:
    """Upsert KPI entries for a given scope and period."""

    metrics = compute_kpis(trades)
    stmt = insert(KPI).values(
        scope=scope,
        scope_ref_id=scope_ref_id,
        period_start=period_start,
        period_end=period_end,
        win_rate=metrics["win_rate"],
        avg_win=metrics["avg_win"],
        avg_loss=metrics["avg_loss"],
        profit_factor=metrics["profit_factor"],
        expectancy=metrics["expectancy"],
        mdd=metrics["mdd"],
        total_trades=metrics["total_trades"],
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[KPI.scope, KPI.scope_ref_id, KPI.period_start, KPI.period_end],
        set_=dict(
            win_rate=stmt.excluded.win_rate,
            avg_win=stmt.excluded.avg_win,
            avg_loss=stmt.excluded.avg_loss,
            profit_factor=stmt.excluded.profit_factor,
            expectancy=stmt.excluded.expectancy,
            mdd=stmt.excluded.mdd,
            total_trades=stmt.excluded.total_trades,
            updated_at=func.now(),
        ),
    )
    db.execute(stmt)
    db.commit()
    kpi = db.scalar(
        select(KPI).where(
            KPI.scope == scope,
            KPI.scope_ref_id == scope_ref_id,
            KPI.period_start == period_start,
            KPI.period_end == period_end,
        )
    )
    assert kpi is not None
    return kpi


def record_equity_curve(db: Session, account: Account, trades: Sequence[Trade]) -> None:
    """Persist daily equity curve values."""

    series = equity_curve(trades)
    for curve_date, equity in series.items():
        stmt = insert(EquityDaily).values(
            account_id=account.id,
            date=curve_date.date(),
            equity=float(equity),
            net_pnl_day=float(series.diff().fillna(series).loc[curve_date]),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[EquityDaily.account_id, EquityDaily.date],
            set_=dict(equity=stmt.excluded.equity, net_pnl_day=stmt.excluded.net_pnl_day),
        )
        db.execute(stmt)
    db.commit()


def assign_strategy(db: Session, trade_id: int, strategy_id: int) -> None:
    """Assign a strategy tag to a trade."""

    strategy = db.get(Strategy, strategy_id)
    trade = db.get(Trade, trade_id)
    if not strategy or not trade:
        raise ValueError("Invalid trade or strategy")
    db.merge(TradeTag(trade_id=trade_id, strategy_id=strategy_id))
    db.commit()
