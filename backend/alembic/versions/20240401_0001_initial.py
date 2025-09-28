"""initial schema"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20240401_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=64)),
        sa.Column("tz", sa.String(length=64), server_default="Asia/Taipei"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "broker_connections",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("broker", sa.Enum("shioaji", "ibkr", "email_csv", name="broker_enum"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="inactive"),
        sa.Column("oauth_token_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_connection_id", sa.BigInteger(), sa.ForeignKey("broker_connections.id")),
        sa.Column("account_code", sa.String(length=64), nullable=False),
        sa.Column("currency", sa.String(length=16), server_default="TWD"),
        sa.Column("nickname", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "symbols",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("ticker", sa.String(length=64), nullable=False),
        sa.Column("exchange", sa.String(length=64)),
        sa.Column("asset_class", sa.Enum("stock", "etf", "futures", "options", name="asset_class_enum")),
        sa.Column("lot_size", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_symbol", "symbols", ["ticker", "exchange"])
    op.create_table(
        "trades",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol_id", sa.BigInteger(), sa.ForeignKey("symbols.id"), nullable=False),
        sa.Column("side", sa.Enum("BUY", "SELL", name="trade_side_enum"), nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("trade_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_id", sa.String(length=128)),
        sa.Column("fee", sa.Numeric(18, 4), server_default="0"),
        sa.Column("tax", sa.Numeric(18, 4), server_default="0"),
        sa.Column("venue", sa.String(length=64)),
        sa.Column("raw_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "positions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol_id", sa.BigInteger(), sa.ForeignKey("symbols.id"), nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("avg_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "cash_activities",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "strategies",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("rules_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_strategy_name", "strategies", ["user_id", "name"])
    op.create_table(
        "trade_tags",
        sa.Column("trade_id", sa.BigInteger(), sa.ForeignKey("trades.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("strategy_id", sa.BigInteger(), sa.ForeignKey("strategies.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_table(
        "equity_daily",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("account_id", sa.BigInteger(), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("equity", sa.Numeric(18, 4), nullable=False),
        sa.Column("net_pnl_day", sa.Numeric(18, 4), nullable=False),
    )
    op.create_unique_constraint("uq_equity_daily", "equity_daily", ["account_id", "date"])
    op.create_table(
        "kpis",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("scope", sa.Enum("account", "strategy", "account_month", "strategy_month", name="kpi_scope_enum"), nullable=False),
        sa.Column("scope_ref_id", sa.BigInteger(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("win_rate", sa.Float()),
        sa.Column("avg_win", sa.Float()),
        sa.Column("avg_loss", sa.Float()),
        sa.Column("profit_factor", sa.Float()),
        sa.Column("expectancy", sa.Float()),
        sa.Column("mdd", sa.Float()),
        sa.Column("total_trades", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_kpi_period", "kpis", ["scope", "scope_ref_id", "period_start", "period_end"])


def downgrade() -> None:
    op.drop_table("kpis")
    op.drop_constraint("uq_equity_daily", "equity_daily", type_="unique")
    op.drop_table("equity_daily")
    op.drop_table("trade_tags")
    op.drop_constraint("uq_strategy_name", "strategies", type_="unique")
    op.drop_table("strategies")
    op.drop_table("cash_activities")
    op.drop_table("positions")
    op.drop_table("trades")
    op.drop_constraint("uq_symbol", "symbols", type_="unique")
    op.drop_table("symbols")
    op.drop_table("accounts")
    op.drop_table("broker_connections")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS broker_enum")
    op.execute("DROP TYPE IF EXISTS trade_side_enum")
    op.execute("DROP TYPE IF EXISTS asset_class_enum")
    op.execute("DROP TYPE IF EXISTS kpi_scope_enum")
