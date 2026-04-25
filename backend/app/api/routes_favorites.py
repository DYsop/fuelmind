from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.session import get_db_session
from app.schemas.station_schema import FavoriteCreateRequest


router = APIRouter(prefix="/favorites", tags=["favorites"], dependencies=[Depends(verify_internal_token)])


@router.get("")
async def list_favorites(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    return await request.app.state.price_service.list_favorites(session)


@router.post("")
async def create_favorite(
    payload: FavoriteCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        favorite = await request.app.state.price_service.add_favorite(session, payload.station_id, payload.label)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"id": favorite.id, "station_id": payload.station_id, "label": favorite.label}


@router.delete("/{favorite_id}")
async def delete_favorite(
    favorite_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        await request.app.state.price_service.delete_favorite(session, favorite_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True}

