from __future__ import annotations

import enum
import os
import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import (
    UUID,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def location_column_type():
    database_url = os.getenv("DATABASE_URL", "").lower()
    if "sqlite" in database_url:
        return String(64)
    return Geometry(geometry_type="POINT", srid=4326)


def make_location_value(lat: float, lng: float):
    wkt = f"POINT({lng} {lat})"
    database_url = os.getenv("DATABASE_URL", "").lower()
    if "sqlite" in database_url:
        return wkt
    return WKTElement(wkt, srid=4326)


class Base(DeclarativeBase):
    pass


class FuelTypeEnum(str, enum.Enum):
    e5 = "e5"
    e10 = "e10"
    diesel = "diesel"


class NotificationChannelEnum(str, enum.Enum):
    none = "none"
    email = "email"
    telegram = "telegram"
    ntfy = "ntfy"
    pushover = "pushover"
    home_assistant = "home_assistant"


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_station_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    house_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    post_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    lng: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    location: Mapped[str] = mapped_column(location_column_type())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(back_populates="station")
    price_changes: Mapped[list["PriceChange"]] = relationship(back_populates="station")
    favorites: Mapped[list["FavoriteStation"]] = relationship(back_populates="station")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), index=True)
    fuel_type: Mapped[FuelTypeEnum] = mapped_column(Enum(FuelTypeEnum), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String(64), default="tankerkoenig")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped[Station] = relationship(back_populates="price_snapshots")


class PriceChange(Base):
    __tablename__ = "price_changes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), index=True)
    e5: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    e10: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    diesel: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String(64), default="tankerkoenig")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped[Station] = relationship(back_populates="price_changes")


class FavoriteStation(Base):
    __tablename__ = "favorite_stations"
    __table_args__ = (UniqueConstraint("station_id", name="uq_favorite_station_station"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), index=True)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    station: Mapped[Station] = relationship(back_populates="favorites")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    fuel_type: Mapped[FuelTypeEnum] = mapped_column(Enum(FuelTypeEnum))
    max_price: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    lng: Mapped[Decimal] = mapped_column(Numeric(10, 7))
    radius_km: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_channel: Mapped[NotificationChannelEnum] = mapped_column(
        Enum(NotificationChannelEnum),
        default=NotificationChannelEnum.none,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    events: Mapped[list["AlertEvent"]] = relationship(back_populates="alert_rule")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_rules.id", ondelete="CASCADE"), index=True)
    station_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), index=True)
    fuel_type: Mapped[FuelTypeEnum] = mapped_column(Enum(FuelTypeEnum))
    price: Mapped[Decimal] = mapped_column(Numeric(6, 3))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    message: Mapped[str] = mapped_column(Text)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    alert_rule: Mapped[AlertRule] = relationship(back_populates="events")


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

