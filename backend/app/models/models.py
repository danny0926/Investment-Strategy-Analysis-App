"""Database models."""
from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(64))
    tz: Mapped[str] = mapped_column(String(64), default="Asia/Taipei")

    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    strategies: Mapped[list["Strategy"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    broker_connections: Mapped[list["BrokerConnection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class BrokerConnection(TimestampMixin, Base):
    __tablename__ = "broker_connections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    broker: Mapped[str] = mapped_column(Enum("shioaji", "ibkr", "email_csv", name="broker_enum"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="inactive")
    oauth_token_json: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="broker_connections")
    accounts: Mapped[list["Account"]] = relationship(back_populates="broker_connection")


class Account(TimestampMixin, Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    broker_connection_id: Mapped[int | None] = mapped_column(ForeignKey("broker_connections.id"))
    account_code: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), default="TWD")
    nickname: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="accounts")
    broker_connection: Mapped[BrokerConnection | None] = relationship(back_populates="accounts")
    trades: Mapped[list["Trade"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    positions: Mapped[list["Position"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    cash_activities: Mapped[list["CashActivity"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    equity_daily: Mapped[list["EquityDaily"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Symbol(TimestampMixin, Base):
    __tablename__ = "symbols"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(64), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(64))
    asset_class: Mapped[str] = mapped_column(Enum("stock", "etf", "futures", "options", name="asset_class_enum"))
    lot_size: Mapped[int] = mapped_column(Integer, default=1)

    trades: Mapped[list["Trade"]] = relationship(back_populates="symbol")

    __table_args__ = (UniqueConstraint("ticker", "exchange", name="uq_symbol"),)


class Trade(TimestampMixin, Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id"), nullable=False)
    side: Mapped[str] = mapped_column(Enum("BUY", "SELL", name="trade_side_enum"), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    trade_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(128))
    fee: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    tax: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    venue: Mapped[str | None] = mapped_column(String(64))
    raw_json: Mapped[dict | None] = mapped_column(JSON)

    account: Mapped[Account] = relationship(back_populates="trades")
    symbol: Mapped[Symbol] = relationship(back_populates="trades")
    strategies: Mapped[list["Strategy"]] = relationship(
        secondary="trade_tags", back_populates="trades", lazy="selectin"
    )


class Position(TimestampMixin, Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    symbol_id: Mapped[int] = mapped_column(ForeignKey("symbols.id"), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    account: Mapped[Account] = relationship(back_populates="positions")
    symbol: Mapped[Symbol] = relationship()


class CashActivity(TimestampMixin, Base):
    __tablename__ = "cash_activities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))

    account: Mapped[Account] = relationship(back_populates="cash_activities")


class Strategy(TimestampMixin, Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rules_json: Mapped[dict | None] = mapped_column(JSON)

    user: Mapped[User] = relationship(back_populates="strategies")
    trades: Mapped[list[Trade]] = relationship(
        secondary="trade_tags", back_populates="strategies", lazy="selectin"
    )

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_strategy_name"),)


class TradeTag(Base):
    __tablename__ = "trade_tags"

    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trades.id", ondelete="CASCADE"), primary_key=True
    )
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), primary_key=True
    )


class EquityDaily(Base):
    __tablename__ = "equity_daily"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    equity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    net_pnl_day: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    account: Mapped[Account] = relationship(back_populates="equity_daily")

    __table_args__ = (UniqueConstraint("account_id", "date", name="uq_equity_daily"),)


class KPI(TimestampMixin, Base):
    __tablename__ = "kpis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    scope: Mapped[str] = mapped_column(
        Enum("account", "strategy", "account_month", "strategy_month", name="kpi_scope_enum"),
        nullable=False,
    )
    scope_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    win_rate: Mapped[float | None] = mapped_column(Float)
    avg_win: Mapped[float | None] = mapped_column(Float)
    avg_loss: Mapped[float | None] = mapped_column(Float)
    profit_factor: Mapped[float | None] = mapped_column(Float)
    expectancy: Mapped[float | None] = mapped_column(Float)
    mdd: Mapped[float | None] = mapped_column(Float)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint(
            "scope", "scope_ref_id", "period_start", "period_end", name="uq_kpi_period"
        ),
    )
