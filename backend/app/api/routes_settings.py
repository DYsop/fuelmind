from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.models import AppSetting
from app.db.session import get_db_session
from app.schemas.analytics_schema import AppSettingsUpdate


router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(verify_internal_token)])


@router.get("")
async def get_settings_status(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    settings = request.app.state.settings
    result = await session.execute(select(AppSetting))
    stored = {item.key: item.value for item in result.scalars().all()}
    return {
        "default_lat": float(stored["default_lat"]) if stored.get("default_lat") else settings.default_lat,
        "default_lng": float(stored["default_lng"]) if stored.get("default_lng") else settings.default_lng,
        "default_radius_km": float(stored.get("default_radius_km", settings.default_radius_km)),
        "default_fuel_type": stored.get("default_fuel_type", settings.default_fuel_type),
        "scheduler_enabled": settings.enable_scheduler,
        "notification_mode": settings.notification_mode,
        "external_api_configured": settings.external_api_configured,
        "allow_public_api": settings.allow_public_api,
        "frontend_api_base_url": settings.frontend_api_base_url,
        "legal_note": (
            "FuelMind ist fuer private, lokale Nutzung gedacht. Tankerkönig- und MTS-K-Bedingungen "
            "sind eigenverantwortlich einzuhalten."
        ),
    }


@router.put("/defaults")
async def update_defaults(
    payload: AppSettingsUpdate,
    session: AsyncSession = Depends(get_db_session),
):
    for key, value in payload.model_dump().items():
        result = await session.execute(select(AppSetting).where(AppSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = "" if value is None else str(value)
        else:
            session.add(AppSetting(key=key, value="" if value is None else str(value)))
    await session.commit()
    return {"saved": True}

