from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.price_schema import RecommendationResponse


FuelType = Literal["e5", "e10", "diesel"]


class StationAnalyticsResponse(BaseModel):
    station_id: str
    fuel_type: FuelType
    average_price: float
    minimum_price: float
    maximum_price: float
    cheapest_hour: int | None = None
    most_expensive_hour: int | None = None
    spread: float
    observation_count: int
    hourly_profile: list[dict]


class BestTimeWindow(BaseModel):
    hour: int
    average_price: float
    sample_count: int


class BestTimeResponse(BaseModel):
    fuel_type: FuelType
    recommended_windows: list[BestTimeWindow]
    reason: str
    confidence: float = Field(ge=0, le=1)
    generated_at: datetime


class AppStatusResponse(BaseModel):
    default_lat: float | None = None
    default_lng: float | None = None
    default_radius_km: float
    default_fuel_type: FuelType
    scheduler_enabled: bool
    notification_mode: str
    external_api_configured: bool
    allow_public_api: bool
    frontend_api_base_url: str
    legal_note: str


class AppSettingsUpdate(BaseModel):
    default_lat: float | None = Field(default=None, ge=-90, le=90)
    default_lng: float | None = Field(default=None, ge=-180, le=180)
    default_radius_km: float = Field(gt=0, le=25)
    default_fuel_type: FuelType


class PredictionEnvelope(BaseModel):
    recommendation: RecommendationResponse
