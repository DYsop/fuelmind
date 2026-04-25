from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.security import verify_internal_token


router = APIRouter(prefix="/locations", tags=["locations"], dependencies=[Depends(verify_internal_token)])


@router.get("/search")
async def search_locations(
    request: Request,
    q: str = Query(min_length=2, max_length=200),
    limit: int | None = Query(default=None, ge=1, le=10),
):
    return await request.app.state.geocoding_service.search(q, limit=limit)
