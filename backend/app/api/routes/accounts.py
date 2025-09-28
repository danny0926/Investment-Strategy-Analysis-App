"""Account and trade endpoints."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, get_db
from app.ingestors.email_csv_ingestor import parse_generic_tw_csv
from app.models.models import Account, KPI, Strategy, Trade
from app.schemas.account import (
    AccountResponse,
    CSVIngestResult,
    KPIQuery,
    KPIResponse,
    StrategyCreate,
    StrategyResponse,
    TagTradeRequest,
    TradeQuery,
    TradeResponse,
)
from app.services.trades import assign_strategy, compute_kpis, record_equity_curve, upsert_trades

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[AccountResponse]:
    """Return user accounts."""

    accounts = db.scalars(select(Account).where(Account.user_id == user.id)).all()
    response: list[AccountResponse] = []
    for acc in accounts:
        broker = acc.broker_connection.broker if acc.broker_connection else None
        response.append(
            AccountResponse(
                id=acc.id,
                account_code=acc.account_code,
                currency=acc.currency,
                nickname=acc.nickname,
                broker=broker,
                created_at=acc.created_at,
            )
        )
    return response


@router.get("/{account_id}/trades", response_model=list[TradeResponse])
def list_trades(
    account_id: int,
    symbol: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> list[TradeResponse]:
    """List trades for an account."""

    query = select(Trade).where(Trade.account_id == account_id)
    if symbol:
        query = query.join(Trade.symbol).where(Trade.symbol.has(ticker=symbol))
    if start:
        query = query.where(Trade.trade_ts >= start)
    if end:
        query = query.where(Trade.trade_ts <= end)
    trades = db.scalars(query.order_by(Trade.trade_ts.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    response = []
    for trade in trades:
        response.append(
            TradeResponse(
                id=trade.id,
                symbol=trade.symbol.ticker,
                side=trade.side,
                qty=float(trade.qty),
                price=float(trade.price),
                trade_ts=trade.trade_ts,
                order_id=trade.order_id,
                fee=float(trade.fee or 0),
                tax=float(trade.tax or 0),
                venue=trade.venue,
                strategy_ids=[s.id for s in trade.strategies],
            )
        )
    return response


@router.post("/{account_id}/strategies", response_model=StrategyResponse)
def create_strategy(
    account_id: int,
    payload: StrategyCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> StrategyResponse:
    """Create strategy tied to account user."""

    account = db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    strategy = Strategy(user_id=user.id, name=payload.name, rules_json=payload.rules_json)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return StrategyResponse.model_validate(strategy)


@router.post("/trades/{trade_id}/tags")
def tag_trade(
    trade_id: int,
    payload: TagTradeRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, str]:
    """Tag a trade with a strategy."""

    trade = db.get(Trade, trade_id)
    if not trade or trade.account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade not found")
    try:
        assign_strategy(db, trade_id, payload.strategy_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "ok"}


@router.post("/{account_id}/upload-csv", response_model=CSVIngestResult)
def upload_csv(
    account_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> CSVIngestResult:
    """Upload CSV broker statement."""

    account = db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    content = file.file.read()
    trades = parse_generic_tw_csv(account_id, content.decode("utf-8"))
    imported = upsert_trades(db, trades)
    account_trades = db.scalars(select(Trade).where(Trade.account_id == account_id)).all()
    record_equity_curve(db, account, account_trades)
    return CSVIngestResult(account_id=account_id, imported_trades=imported, ignored_rows=0)


@router.get("/{account_id}/kpis", response_model=KPIResponse)
def account_kpis(
    account_id: int,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> KPIResponse:
    """Return KPI summary for account."""

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


@router.get("/{account_id}/export/excel")
def export_excel(
    account_id: int,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> StreamingResponse:
    """Export trades to Excel matching template."""

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
    data = [
        {
            "日期": trade.trade_ts.strftime("%Y-%m-%d"),
            "代碼": trade.symbol.ticker,
            "股數": float(trade.qty),
            "均價": float(trade.price),
            "賣出價": float(trade.price) if trade.side == "SELL" else 0,
            "投入成本": float(trade.qty) * float(trade.price) if trade.side == "BUY" else 0,
            "損益": float(trade.price) * float(trade.qty) * (1 if trade.side == "SELL" else -1)
            - float(trade.fee or 0)
            - float(trade.tax or 0),
        }
        for trade in trades
    ]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Trades")
    output.seek(0)
    headers = {"Content-Disposition": f"attachment; filename=account-{account_id}.xlsx"}
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)
