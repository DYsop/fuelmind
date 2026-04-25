from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LocationSearchItem(BaseModel):
    label: str
    lat: float
    lng: float
    city: str | None = None
    post_code: str | None = None
    street: str | None = None
    house_number: str | None = None


class LocationSearchResponse(BaseModel):
    items: list[LocationSearchItem]
    source: str = "nominatim"
    cached: bool = False
    fetched_at: datetime
