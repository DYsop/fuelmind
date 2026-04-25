from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.session import get_db_session
from app.schemas.station_schema import NearbySearchRequest


router = APIRouter(prefix="/stations", tags=["stations"], dependencies=[Depends(verify_internal_token)])


@router.get("/nearby")
async def nearby_stations(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(gt=0, le=25),
    fuel_type: str = Query(pattern="^(e5|e10|diesel|all)$"),
    sort: str = Query(pattern="^(price|distance)$"),
):
    return await request.app.state.station_service.search_nearby(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        fuel_type=fuel_type,
        sort=sort,
    )


@router.get("/{station_id}")
async def station_detail(
    station_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        return await request.app.state.station_service.get_station_detail(session, station_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sync-nearby")
async def sync_nearby(
    payload: NearbySearchRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    return await request.app.state.station_service.sync_nearby(
        session,
        lat=payload.lat,
        lng=payload.lng,
        radius_km=payload.radius_km,
        fuel_type=payload.fuel_type,
        sort=payload.sort,
    )

