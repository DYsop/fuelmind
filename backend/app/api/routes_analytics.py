from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.session import get_db_session


router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(verify_internal_token)])


@router.get("/station/{station_id}")
async def station_analytics(
    request: Request,
    station_id: str,
    fuel_type: str = Query(pattern="^(e5|e10|diesel)$"),
    days: int = Query(default=7, ge=1, le=60),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await request.app.state.analytics_service.station_analytics(
            session,
            station_id=station_id,
            fuel_type=fuel_type,
            days=days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/best-time")
async def best_time(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(gt=0, le=25),
    fuel_type: str = Query(pattern="^(e5|e10|diesel)$"),
    session: AsyncSession = Depends(get_db_session),
):
    return await request.app.state.analytics_service.best_time(
        session,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        fuel_type=fuel_type,
    )

