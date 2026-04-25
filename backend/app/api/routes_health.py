from __future__ import annotations

from fastapi import APIRouter, Request

from app.db.session import db_ping


router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    database_status = "ok"
    redis_status = "ok"
    try:
        await db_ping()
    except Exception:
        database_status = "error"

    redis_client = request.app.state.redis
    if redis_client:
        try:
            await redis_client.ping()
        except Exception:
            redis_status = "error"
    else:
        redis_status = "unavailable"

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "database": database_status,
        "redis": redis_status,
        "external_api_configured": request.app.state.settings.external_api_configured,
    }

