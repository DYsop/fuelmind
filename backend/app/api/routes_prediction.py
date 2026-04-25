from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.session import get_db_session


router = APIRouter(prefix="/prediction", tags=["prediction"], dependencies=[Depends(verify_internal_token)])


@router.get("/recommendation")
async def recommendation(
    request: Request,
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(gt=0, le=25),
    fuel_type: str = Query(pattern="^(e5|e10|diesel)$"),
    session: AsyncSession = Depends(get_db_session),
):
    return await request.app.state.prediction_service.get_recommendation(
        session,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        fuel_type=fuel_type,
    )

