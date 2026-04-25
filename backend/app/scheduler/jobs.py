from __future__ import annotations

from app.core.logging import get_logger
from app.db.session import SessionLocal


logger = get_logger(__name__)


async def sync_favorites_prices(app) -> None:
    async with SessionLocal() as session:
        created = await app.state.price_service.refresh_favorite_snapshots(session)
        logger.info("Favoritenpreise synchronisiert", extra={"job": "sync_favorites_prices", "status": created})


async def check_alerts(app) -> None:
    async with SessionLocal() as session:
        result = await app.state.alert_service.check_alerts(session)
        logger.info("Alerts geprueft", extra={"job": "check_alerts", "status": result["events_created"]})


async def cleanup_old_cache(app) -> None:
    redis_client = app.state.redis
    if not redis_client:
        return
    await redis_client.execute_command("BGSAVE")
    logger.info("Redis-Cache gewartet", extra={"job": "cleanup_old_cache", "status": "ok"})

