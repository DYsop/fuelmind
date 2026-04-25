from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceSnapshot
from app.services.station_service import StationService


class AnalyticsService:
    def __init__(self, station_service: StationService) -> None:
        self.station_service = station_service

    async def station_analytics(
        self,
        session: AsyncSession,
        *,
        station_id: str,
        fuel_type: str,
        days: int,
    ) -> dict[str, Any]:
        station = await self.station_service.get_station_by_external_id(session, station_id)
        if station is None:
            raise ValueError("Tankstelle nicht gefunden.")
        since = datetime.now(UTC) - timedelta(days=days)
        result = await session.execute(
            select(PriceSnapshot)
            .where(
                PriceSnapshot.station_id == station.id,
                PriceSnapshot.fuel_type == fuel_type,
                PriceSnapshot.observed_at >= since,
            )
            .order_by(PriceSnapshot.observed_at.asc())
        )
        snapshots = result.scalars().all()
        if not snapshots:
            return {
                "station_id": station_id,
                "fuel_type": fuel_type,
                "average_price": 0.0,
                "minimum_price": 0.0,
                "maximum_price": 0.0,
                "cheapest_hour": None,
                "most_expensive_hour": None,
                "spread": 0.0,
                "observation_count": 0,
                "hourly_profile": [],
            }

        prices = [float(item.price) for item in snapshots]
        by_hour: dict[int, list[float]] = defaultdict(list)
        for item in snapshots:
            by_hour[item.observed_at.hour].append(float(item.price))
        hourly_profile = [
            {
                "hour": hour,
                "average_price": round(mean(values), 3),
                "minimum_price": round(min(values), 3),
                "sample_count": len(values),
            }
            for hour, values in sorted(by_hour.items())
        ]
        cheapest_hour = min(hourly_profile, key=lambda item: item["average_price"])["hour"]
        most_expensive_hour = max(hourly_profile, key=lambda item: item["average_price"])["hour"]
        return {
            "station_id": station_id,
            "fuel_type": fuel_type,
            "average_price": round(mean(prices), 3),
            "minimum_price": round(min(prices), 3),
            "maximum_price": round(max(prices), 3),
            "cheapest_hour": cheapest_hour,
            "most_expensive_hour": most_expensive_hour,
            "spread": round(max(prices) - min(prices), 3),
            "observation_count": len(prices),
            "hourly_profile": hourly_profile,
        }

    async def best_time(
        self,
        session: AsyncSession,
        *,
        lat: float,
        lng: float,
        radius_km: float,
        fuel_type: str,
    ) -> dict[str, Any]:
        stations = await self.station_service.stations_within_radius(
            session,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
        )
        if not stations:
            return {
                "fuel_type": fuel_type,
                "recommended_windows": [],
                "reason": "Noch keine historischen Daten fuer diesen Suchbereich vorhanden.",
                "confidence": 0.1,
                "generated_at": datetime.now(UTC),
            }

        station_ids = [station.id for station in stations]
        since = datetime.now(UTC) - timedelta(days=14)
        result = await session.execute(
            select(PriceSnapshot)
            .where(
                PriceSnapshot.station_id.in_(station_ids),
                PriceSnapshot.fuel_type == fuel_type,
                PriceSnapshot.observed_at >= since,
            )
            .order_by(PriceSnapshot.observed_at.asc())
        )
        snapshots = result.scalars().all()
        if not snapshots:
            return {
                "fuel_type": fuel_type,
                "recommended_windows": [],
                "reason": "Fuer diesen Kraftstofftyp liegen noch keine ausreichenden Beobachtungen vor.",
                "confidence": 0.15,
                "generated_at": datetime.now(UTC),
            }

        by_hour: dict[int, list[float]] = defaultdict(list)
        for snapshot in snapshots:
            by_hour[snapshot.observed_at.hour].append(float(snapshot.price))

        ranked = sorted(
            (
                {
                    "hour": hour,
                    "average_price": round(mean(values), 3),
                    "sample_count": len(values),
                }
                for hour, values in by_hour.items()
            ),
            key=lambda item: (item["average_price"], -item["sample_count"]),
        )
        windows = ranked[:3]
        confidence = min(0.9, 0.25 + len(snapshots) / 500)
        reason = (
            "Die Empfehlung basiert auf historischen Stundenmittelwerten der letzten 14 Tage "
            "im gespeicherten Suchradius."
        )
        return {
            "fuel_type": fuel_type,
            "recommended_windows": windows,
            "reason": reason,
            "confidence": round(confidence, 2),
            "generated_at": datetime.now(UTC),
        }

