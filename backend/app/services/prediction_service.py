from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceSnapshot
from app.services.analytics_service import AnalyticsService
from app.services.price_service import PriceService
from app.services.station_service import StationService


class PredictionService:
    def __init__(
        self,
        price_service: PriceService,
        analytics_service: AnalyticsService,
        station_service: StationService,
    ) -> None:
        self.price_service = price_service
        self.analytics_service = analytics_service
        self.station_service = station_service

    async def get_recommendation(
        self,
        session: AsyncSession,
        *,
        lat: float,
        lng: float,
        radius_km: float,
        fuel_type: str,
    ) -> dict[str, Any]:
        cheapest = await self.price_service.get_cheapest_stations(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            fuel_type=fuel_type,
            limit=1,
        )
        if not cheapest["items"]:
            return {
                "recommendation": "neutral",
                "reason": "Aktuell liegen fuer diesen Bereich keine verarbeitbaren Preisdaten vor.",
                "confidence": 0.2,
                "best_station": None,
                "estimated_saving": None,
            }

        best_station = cheapest["items"][0]
        station = await self.station_service.get_station_by_external_id(session, best_station["station_id"])
        if station is None:
            return {
                "recommendation": "neutral",
                "reason": "Die Tankstelle wurde noch nicht lokal gespeichert und kann nicht bewertet werden.",
                "confidence": 0.2,
                "best_station": best_station,
                "estimated_saving": None,
            }

        since_7d = datetime.now(UTC) - timedelta(days=7)
        since_24h = datetime.now(UTC) - timedelta(hours=24)
        result = await session.execute(
            select(PriceSnapshot)
            .where(
                PriceSnapshot.station_id == station.id,
                PriceSnapshot.fuel_type == fuel_type,
                PriceSnapshot.observed_at >= since_7d,
            )
            .order_by(PriceSnapshot.observed_at.asc())
        )
        snapshots = result.scalars().all()
        if len(snapshots) < 8:
            return {
                "recommendation": "neutral",
                "reason": "Es liegen noch nicht genug historische Daten fuer eine belastbare Heuristik vor.",
                "confidence": 0.25,
                "best_station": best_station,
                "estimated_saving": None,
            }

        prices = sorted(float(snapshot.price) for snapshot in snapshots)
        current_price = float(best_station["price"])
        average_7d = mean(prices)
        percentile_25 = prices[max(0, int(len(prices) * 0.25) - 1)]
        last_24h = [float(snapshot.price) for snapshot in snapshots if snapshot.observed_at >= since_24h]
        min_24h = min(last_24h) if last_24h else min(prices)

        best_time = await self.analytics_service.best_time(
            session,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            fuel_type=fuel_type,
        )
        future_window_cheaper = any(window["average_price"] + 0.005 < current_price for window in best_time["recommended_windows"])

        if current_price <= percentile_25 or current_price <= min_24h + 0.01:
            return {
                "recommendation": "tank_now",
                "reason": (
                    f"Der aktuelle {fuel_type.upper()}-Preis liegt bei {current_price:.3f} EUR und damit "
                    f"unter dem 25%-Quantil der letzten 7 Tage ({percentile_25:.3f} EUR)."
                ),
                "confidence": 0.78,
                "best_station": best_station,
                "estimated_saving": round(max(0.0, average_7d - current_price), 3),
            }

        if current_price > average_7d + 0.03 and future_window_cheaper:
            return {
                "recommendation": "wait",
                "reason": (
                    f"Der aktuelle {fuel_type.upper()}-Preis liegt mit {current_price:.3f} EUR deutlich ueber dem "
                    f"7-Tage-Durchschnitt von {average_7d:.3f} EUR, waehrend historische guenstigere Zeitfenster "
                    "in den naechsten Stunden auftreten."
                ),
                "confidence": 0.7,
                "best_station": best_station,
                "estimated_saving": round(current_price - average_7d, 3),
            }

        return {
            "recommendation": "neutral",
            "reason": (
                f"Der aktuelle Preis von {current_price:.3f} EUR liegt in einem normalen Bereich rund um den "
                f"7-Tage-Durchschnitt von {average_7d:.3f} EUR."
            ),
            "confidence": 0.5,
            "best_station": best_station,
            "estimated_saving": round(abs(average_7d - current_price), 3),
        }
