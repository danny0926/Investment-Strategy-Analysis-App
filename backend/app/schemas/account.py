"""Account related schemas."""
from __future__ import annotations

from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, Field


class AccountResponse(BaseModel):
    """Basic account info."""

    id: int
    account_code: str
    currency: str
    nickname: Optional[str]
    broker: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class TradeBase(BaseModel):
    symbol: str
    side: str
    qty: float
    price: float
    trade_ts: datetime
    order_id: str | None = None
    fee: float | None = None
    tax: float | None = None
    venue: str | None = None


class TradeResponse(TradeBase):
    id: int
    strategy_ids: list[int] = Field(default_factory=list)


class TradeQuery(BaseModel):
    account_id: int
    symbol: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    page: int = 1
    page_size: int = 50


class EquityPoint(BaseModel):
    date: date
    equity: float
    net_pnl_day: float


class KPIResponse(BaseModel):
    scope: str
    scope_ref_id: int
    period_start: datetime
    period_end: datetime
    win_rate: float | None
    avg_win: float | None
    avg_loss: float | None
    profit_factor: float | None
    expectancy: float | None
    mdd: float | None
    total_trades: int


class KPIQuery(BaseModel):
    scope: str
    scope_ref_id: int
    start: datetime
    end: datetime


class StrategyCreate(BaseModel):
    name: str
    rules_json: dict | None = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    rules_json: dict | None

    class Config:
        orm_mode = True


class TagTradeRequest(BaseModel):
    strategy_id: int


class CSVIngestResult(BaseModel):
    account_id: int
    imported_trades: int
    ignored_rows: int
