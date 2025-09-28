"""Seed demo data for the trade journal."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random

from sqlalchemy import select

from app.db.session import session_scope
from app.models.models import Account, Symbol, Trade, User
from app.services.security import get_password_hash


def ensure_demo_user() -> User:
    with session_scope() as session:
        user = session.scalar(select(User).where(User.email == "demo@example.com"))
        if user:
            return user
        user = User(email="demo@example.com", password_hash=get_password_hash("demo123"), tz="Asia/Taipei")
        session.add(user)
        session.flush()
        account = Account(user_id=user.id, account_code="DEMO-001", currency="TWD", nickname="Demo Account")
        session.add(account)
        session.commit()
        return user


def seed_trades(user: User) -> None:
    with session_scope() as session:
        account = session.scalar(select(Account).where(Account.user_id == user.id))
        if not account:
            return
        symbol = session.scalar(select(Symbol).where(Symbol.ticker == "2330.TW"))
        if symbol is None:
            symbol = Symbol(ticker="2330.TW", exchange="TWSE", asset_class="stock", lot_size=1000)
            session.add(symbol)
            session.flush()
        now = datetime.now(timezone.utc)
        for day in range(30):
            ts = now - timedelta(days=day)
            side = "SELL" if day % 2 == 0 else "BUY"
            price = 600 + random.uniform(-5, 5)
            qty = 1
            trade = Trade(
                account_id=account.id,
                symbol_id=symbol.id,
                side=side,
                qty=qty,
                price=price,
                trade_ts=ts,
                fee=5,
                tax=2,
            )
            session.add(trade)
        session.commit()


if __name__ == "__main__":
    user = ensure_demo_user()
    seed_trades(user)
    print("Seed complete")
