from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.session import get_db_session


router = APIRouter(prefix="/prices", tags=["prices"], dependencies=[Depends(verify_internal_token)])


@router.get("/current")
async def current_prices(
    request: Request,
    station_ids: str = Query(min_length=1),
    fuel_type: str | None = Query(default=None, pattern="^(e5|e10|diesel)?$"),
    session: AsyncSession = Depends(get_db_session),
):
    station_id_list = [item.strip() for item in station_ids.split(",") if item.strip()]
    if len(station_id_list) > 10:
        raise HTTPException(status_code=400, detail="Es duerfen maximal 10 Tankstellen gleichzeitig abgefragt werden.")
    return await request.app.state.price_service.get_current_prices(session, station_id_list, fuel_type)


@router.get("/history/{station_id}")
async def price_history(
    request: Request,
    station_id: str,
    fuel_type: str = Query(pattern="^(e5|e10|diesel)$"),
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await request.app.state.price_service.get_price_history(
            session,
            station_id,
            fuel_type,
            from_date,
            to_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/cheapest")
async def cheapest_prices(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(gt=0, le=25),
    fuel_type: str = Query(pattern="^(e5|e10|diesel)$"),
    limit: int = Query(default=5, ge=1, le=20),
):
    return await request.app.state.price_service.get_cheapest_stations(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        fuel_type=fuel_type,
        limit=limit,
    )

