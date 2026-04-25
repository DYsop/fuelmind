from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler.jobs import check_alerts, cleanup_old_cache, sync_favorites_prices


def build_scheduler(app) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(sync_favorites_prices, "interval", minutes=10, args=[app], id="sync_favorites_prices")
    scheduler.add_job(check_alerts, "interval", minutes=5, args=[app], id="check_alerts")
    scheduler.add_job(cleanup_old_cache, "interval", days=1, args=[app], id="cleanup_old_cache")
    return scheduler

