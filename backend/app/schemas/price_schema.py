from __future__ import annotations

from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, Field


FuelType = Literal["e5", "e10", "diesel"]


class CurrentPricesResponse(BaseModel):
    items: list[dict]
    fetched_at: datetime
    source: str = "tankerkoenig"


class PriceHistoryItem(BaseModel):
    observed_at: datetime
    price: float
    is_open: bool
    source: str


class PriceHistoryResponse(BaseModel):
    station_id: str
    fuel_type: FuelType
    items: list[PriceHistoryItem]


class CheapestStationsResponse(BaseModel):
    items: list[dict]
    fuel_type: FuelType
    fetched_at: datetime


class HourlyAggregate(BaseModel):
    hour: time
    average_price: float
    min_price: float
    sample_count: int


class RecommendationResponse(BaseModel):
    recommendation: Literal["tank_now", "wait", "neutral"]
    reason: str
    confidence: float = Field(ge=0, le=1)
    best_station: dict | None = None
    estimated_saving: float | None = None

