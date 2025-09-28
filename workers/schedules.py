"""APScheduler worker to run daily ingestion tasks."""
from __future__ import annotations

from datetime import datetime, timedelta

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.settings import settings
from app.db.session import SessionLocal
from app.models.models import Account
from app.services.trades import record_equity_curve, upsert_trades
from app.ingestors import shioaji_ingestor, ibkr_ingestor


scheduler = BlockingScheduler(timezone=settings.timezone)


def daily_sync_job() -> None:
    """Fetch trades from brokers and recompute KPIs."""

    with SessionLocal() as session:
        accounts = session.scalars(select(Account)).all()
        start = datetime.now().date() - timedelta(days=1)
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(start, datetime.max.time())
        for account in accounts:
            trades = []
            if account.broker_connection and account.broker_connection.broker == "shioaji":
                trades.extend(shioaji_ingestor.fetch_trades(account, start_dt, end_dt))
            elif account.broker_connection and account.broker_connection.broker == "ibkr":
                trades.extend(ibkr_ingestor.fetch_trades(account, start_dt, end_dt))
            imported = upsert_trades(session, trades)
            if imported:
                session.refresh(account)
                record_equity_curve(session, account, account.trades)


scheduler.add_job(daily_sync_job, CronTrigger(hour=16, minute=30))


if __name__ == "__main__":  # pragma: no cover
    scheduler.start()
