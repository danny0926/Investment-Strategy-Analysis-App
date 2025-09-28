"""Ingestion endpoints for broker connectors."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user, get_db
from app.ingestors import ibkr_ingestor, shioaji_ingestor
from app.models.models import Account
from app.services.trades import record_equity_curve, upsert_trades

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/broker/{broker}")
def ingest_broker(
    broker: str,
    account_id: int,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, int]:
    """Fetch trades from connected brokers."""

    account = db.get(Account, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if broker == "shioaji":
        trades = shioaji_ingestor.fetch_trades(account, start, end)
    elif broker == "ibkr":
        trades = ibkr_ingestor.fetch_trades(account, start, end)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported broker")
    imported = upsert_trades(db, trades)
    account_trades = account.trades
    record_equity_curve(db, account, account_trades)
    return {"imported": imported}
