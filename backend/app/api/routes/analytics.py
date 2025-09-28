"""Analytics endpoints for KPIs and equity."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, get_db
from app.models.models import Account, EquityDaily, KPI, Trade
from app.schemas.account import EquityPoint, KPIResponse
from app.services.trades import compute_kpis

router = APIRouter(tags=["analytics"])


@router.get("/kpis/summary", response_model=KPIResponse)
def kpi_summary(
    scope: str,
    account_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> KPIResponse:
    """Return KPI summary for given scope."""

    if scope != "account":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only account scope supported in MVP")
    if account_id is None or start is None or end is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing parameters")
    account = db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    trades = db.scalars(
        select(Trade).where(
            Trade.account_id == account_id,
            Trade.trade_ts >= start,
            Trade.trade_ts <= end,
        )
    ).all()
    metrics = compute_kpis(trades)
    return KPIResponse(
        scope="account",
        scope_ref_id=account_id,
        period_start=start,
        period_end=end,
        **metrics,
    )


@router.get("/equity/daily", response_model=list[EquityPoint])
def equity_daily(
    account_id: int,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[EquityPoint]:
    """Return equity curve points for account."""

    account = db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    rows = db.scalars(
        select(EquityDaily).where(
            EquityDaily.account_id == account_id,
            EquityDaily.date >= start.date(),
            EquityDaily.date <= end.date(),
        ).order_by(EquityDaily.date)
    ).all()
    return [EquityPoint(date=row.date, equity=float(row.equity), net_pnl_day=float(row.net_pnl_day)) for row in rows]
