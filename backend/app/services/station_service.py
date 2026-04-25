from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import FavoriteStation, PriceSnapshot, Station, make_location_value
from app.services.tankerkoenig_client import TankerkoenigClient, TankerkoenigConfigurationError


logger = get_logger(__name__)


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * radius * asin(sqrt(a))


class StationService:
    def __init__(self, tanker_client: TankerkoenigClient) -> None:
        self.tanker_client = tanker_client

    async def search_nearby(
        self,
        *,
        lat: float,
        lng: float,
        radius_km: float,
        fuel_type: str,
        sort: str,
    ) -> dict[str, Any]:
        return await self.tanker_client.get_nearby_stations(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            fuel_type=fuel_type,
            sort=sort,
        )

    async def sync_nearby(
        self,
        session: AsyncSession,
        *,
        lat: float,
        lng: float,
        radius_km: float,
        fuel_type: str,
        sort: str,
    ) -> dict[str, Any]:
        result = await self.search_nearby(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            fuel_type=fuel_type,
            sort=sort,
        )
        snapshots_created = 0
        for item in result["items"]:
            station = await self.upsert_station(session, item)
            snapshots_created += await self.save_price_snapshots(session, station, item, observed_at=result["fetched_at"])
        await session.commit()
        return {
            "synced_stations": len(result["items"]),
            "snapshots_created": snapshots_created,
            "fetched_at": result["fetched_at"],
            "source": result["source"],
        }

    async def get_station_detail(self, session: AsyncSession, station_id: str) -> dict[str, Any]:
        station = await self.get_station_by_external_id(session, station_id)
        latest_prices = await self._latest_prices_for_station(session, station.id) if station else {}

        try:
            detail = await self.tanker_client.get_station_detail(station_id)
        except TankerkoenigConfigurationError:
            if not station:
                raise
            return self._build_station_detail_from_db(station, latest_prices)

        if station:
            await self.upsert_station(session, detail)
        else:
            station = await self.upsert_station(session, detail)
        await self.save_price_snapshots(session, station, detail | detail.get("prices", {}), observed_at=datetime.now(UTC))
        await session.commit()
        return {
            **detail,
            "prices": {
                "e5": detail["prices"].get("e5"),
                "e10": detail["prices"].get("e10"),
                "diesel": detail["prices"].get("diesel"),
            },
            "source": "tankerkoenig",
        }

    async def get_station_by_external_id(self, session: AsyncSession, station_id: str) -> Station | None:
        result = await session.execute(select(Station).where(Station.external_station_id == station_id))
        return result.scalar_one_or_none()

    async def upsert_station(self, session: AsyncSession, payload: dict[str, Any]) -> Station:
        station = await self.get_station_by_external_id(session, payload["station_id"])
        if station is None:
            station = Station(
                external_station_id=payload["station_id"],
                name=payload["name"],
                brand=payload.get("brand"),
                street=payload.get("street"),
                house_number=payload.get("house_number"),
                post_code=payload.get("post_code"),
                city=payload.get("city"),
                lat=Decimal(str(payload["lat"])),
                lng=Decimal(str(payload["lng"])),
                location=make_location_value(payload["lat"], payload["lng"]),
                is_active=True,
            )
            session.add(station)
            await session.flush()
            return station

        station.name = payload["name"]
        station.brand = payload.get("brand")
        station.street = payload.get("street")
        station.house_number = payload.get("house_number")
        station.post_code = payload.get("post_code")
        station.city = payload.get("city")
        station.lat = Decimal(str(payload["lat"]))
        station.lng = Decimal(str(payload["lng"]))
        station.location = make_location_value(payload["lat"], payload["lng"])
        station.is_active = True
        await session.flush()
        return station

    async def save_price_snapshots(
        self,
        session: AsyncSession,
        station: Station,
        payload: dict[str, Any],
        *,
        observed_at: datetime,
    ) -> int:
        snapshots_created = 0
        prices = payload.get("prices") if "prices" in payload else payload
        for fuel_type in ("e5", "e10", "diesel"):
            price = prices.get(fuel_type)
            if price in (None, False):
                continue
            snapshot = PriceSnapshot(
                station_id=station.id,
                fuel_type=fuel_type,
                price=Decimal(str(price)),
                is_open=bool(payload.get("is_open", payload.get("isOpen", True))),
                observed_at=observed_at,
                source="tankerkoenig",
            )
            session.add(snapshot)
            snapshots_created += 1
        await session.flush()
        return snapshots_created

    async def list_favorite_station_ids(self, session: AsyncSession) -> list[str]:
        result = await session.execute(select(FavoriteStation).join(Station).order_by(FavoriteStation.created_at))
        favorites = result.scalars().all()
        return [favorite.station.external_station_id for favorite in favorites if favorite.station]

    async def stations_within_radius(
        self,
        session: AsyncSession,
        *,
        lat: float,
        lng: float,
        radius_km: float,
    ) -> list[Station]:
        result = await session.execute(select(Station).where(Station.is_active.is_(True)))
        stations = result.scalars().all()
        return [
            station
            for station in stations
            if haversine_km(lat, lng, float(station.lat), float(station.lng)) <= radius_km
        ]

    async def _latest_prices_for_station(self, session: AsyncSession, station_id) -> dict[str, float]:
        result = await session.execute(
            select(PriceSnapshot).where(PriceSnapshot.station_id == station_id).order_by(PriceSnapshot.observed_at.desc())
        )
        items = result.scalars().all()
        latest: dict[str, float] = {}
        for item in items:
            if item.fuel_type.value not in latest:
                latest[item.fuel_type.value] = float(item.price)
        return latest

    def _build_station_detail_from_db(self, station: Station, latest_prices: dict[str, float]) -> dict[str, Any]:
        return {
            "station_id": station.external_station_id,
            "name": station.name,
            "brand": station.brand,
            "address": ", ".join(
                part
                for part in [
                    " ".join(part for part in [station.street, station.house_number] if part),
                    " ".join(part for part in [station.post_code, station.city] if part),
                ]
                if part
            ),
            "lat": float(station.lat),
            "lng": float(station.lng),
            "is_open": None,
            "prices": latest_prices,
            "opening_times": [],
            "overrides": [],
            "source": "database",
        }

