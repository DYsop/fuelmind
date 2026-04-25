from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


FuelType = Literal["e5", "e10", "diesel"]
FuelTypeWithAll = Literal["e5", "e10", "diesel", "all"]
SortType = Literal["price", "distance"]


class NearbySearchRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius_km: float = Field(gt=0, le=25)
    fuel_type: FuelTypeWithAll = "e10"
    sort: SortType = "price"


class StationPriceInfo(BaseModel):
    e5: float | None = None
    e10: float | None = None
    diesel: float | None = None


class StationListItem(BaseModel):
    station_id: str
    name: str
    brand: str | None = None
    price: float | None = None
    fuel_type: FuelTypeWithAll
    distance_km: float | None = None
    is_open: bool | None = None
    address: str
    lat: float
    lng: float


class StationDetailResponse(BaseModel):
    station_id: str
    name: str
    brand: str | None = None
    address: str
    lat: float
    lng: float
    is_open: bool | None = None
    prices: StationPriceInfo
    opening_times: list[dict] = Field(default_factory=list)
    overrides: list[dict] = Field(default_factory=list)
    source: str = "tankerkoenig"


class StationListResponse(BaseModel):
    items: list[StationListItem]
    source: str = "tankerkoenig"
    cached: bool = False
    fetched_at: datetime


class SyncNearbyResponse(BaseModel):
    synced_stations: int
    snapshots_created: int
    fetched_at: datetime
    source: str = "tankerkoenig"


class FavoriteCreateRequest(BaseModel):
    station_id: str
    label: str | None = Field(default=None, max_length=120)


class FavoriteItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    station_id: str
    label: str | None
    name: str
    brand: str | None = None
    address: str
    latest_price: float | None = None
    latest_fuel_type: FuelType | None = None
    latest_snapshot_at: datetime | None = None

