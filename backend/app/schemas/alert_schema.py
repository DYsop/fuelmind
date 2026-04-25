from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


FuelType = Literal["e5", "e10", "diesel"]
NotificationMode = Literal["none", "email", "telegram", "ntfy", "pushover", "home_assistant"]


class AlertRuleBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    fuel_type: FuelType
    max_price: float = Field(gt=0)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius_km: float = Field(gt=0, le=25)
    enabled: bool = True
    notification_channel: NotificationMode = "none"


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(AlertRuleBase):
    pass


class AlertRuleRead(AlertRuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime | None = None


class AlertEventRead(BaseModel):
    id: UUID
    alert_rule_id: UUID
    station_id: str
    station_name: str
    fuel_type: FuelType
    price: float
    triggered_at: datetime
    message: str
    delivered: bool
    delivered_at: datetime | None = None


class AlertCheckResponse(BaseModel):
    checked_rules: int
    events_created: int
    checked_at: datetime

