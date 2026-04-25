from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FavoriteStation, PriceChange, PriceSnapshot, Station
from app.services.station_service import StationService
from app.services.tankerkoenig_client import TankerkoenigClient


class PriceService:
    def __init__(self, tanker_client: TankerkoenigClient, station_service: StationService) -> None:
        self.tanker_client = tanker_client
        self.station_service = station_service

    async def get_current_prices(
        self,
        session: AsyncSession,
        station_ids: list[str],
        fuel_type: str | None = None,
    ) -> dict[str, Any]:
        result = await self.tanker_client.get_prices(station_ids)
        items: list[dict[str, Any]] = []
        observed_at = result["fetched_at"]
        for external_station_id, values in result["items"].items():
            station = await self.station_service.get_station_by_external_id(session, external_station_id)
            if station:
                await self.station_service.save_price_snapshots(
                    session,
                    station,
                    values,
                    observed_at=observed_at,
                )
                await self.record_price_change(session, station, values, observed_at)

            item = {
                "station_id": external_station_id,
                "is_open": values["is_open"],
                "status": values["status"],
                "e5": values.get("e5"),
                "e10": values.get("e10"),
                "diesel": values.get("diesel"),
            }
            if fuel_type:
                item["price"] = values.get(fuel_type)
            items.append(item)

        await session.commit()
        return {
            "items": items,
            "fetched_at": observed_at,
            "source": result["source"],
        }

    async def get_price_history(
        self,
        session: AsyncSession,
        station_id: str,
        fuel_type: str,
        from_date: datetime | None,
        to_date: datetime | None,
    ) -> dict[str, Any]:
        station = await self.station_service.get_station_by_external_id(session, station_id)
        if station is None:
            raise ValueError("Tankstelle nicht gefunden.")

        query = (
            select(PriceSnapshot)
            .where(PriceSnapshot.station_id == station.id, PriceSnapshot.fuel_type == fuel_type)
            .order_by(PriceSnapshot.observed_at.asc())
        )
        if from_date:
            query = query.where(PriceSnapshot.observed_at >= from_date)
        if to_date:
            query = query.where(PriceSnapshot.observed_at <= to_date)
        result = await session.execute(query)
        items = result.scalars().all()
        return {
            "station_id": station_id,
            "fuel_type": fuel_type,
            "items": [
                {
                    "observed_at": item.observed_at,
                    "price": float(item.price),
                    "is_open": item.is_open,
                    "source": item.source,
                }
                for item in items
            ],
        }

    async def get_cheapest_stations(
        self,
        *,
        lat: float,
        lng: float,
        radius_km: float,
        fuel_type: str,
        limit: int,
    ) -> dict[str, Any]:
        nearby = await self.station_service.search_nearby(
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            fuel_type=fuel_type,
            sort="price",
        )
        items = [item for item in nearby["items"] if item.get("price") is not None][:limit]
        return {
            "items": items,
            "fuel_type": fuel_type,
            "fetched_at": nearby["fetched_at"],
        }

    async def list_favorites(self, session: AsyncSession) -> list[dict[str, Any]]:
        result = await session.execute(
            select(FavoriteStation, Station).join(Station).order_by(FavoriteStation.created_at.desc())
        )
        rows = result.all()
        items: list[dict[str, Any]] = []
        for favorite, station in rows:
            latest = await self.get_latest_snapshot(session, station.id)
            items.append(
                {
                    "id": favorite.id,
                    "station_id": station.external_station_id,
                    "label": favorite.label,
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
                    "latest_price": float(latest.price) if latest else None,
                    "latest_fuel_type": latest.fuel_type.value if latest else None,
                    "latest_snapshot_at": latest.observed_at if latest else None,
                }
            )
        return items

    async def add_favorite(self, session: AsyncSession, station_id: str, label: str | None) -> FavoriteStation:
        station = await self.station_service.get_station_by_external_id(session, station_id)
        if station is None:
            detail = await self.tanker_client.get_station_detail(station_id)
            station = await self.station_service.upsert_station(session, detail)
            await self.station_service.save_price_snapshots(session, station, detail, observed_at=datetime.now(UTC))

        existing = await session.execute(select(FavoriteStation).where(FavoriteStation.station_id == station.id))
        favorite = existing.scalar_one_or_none()
        if favorite:
            favorite.label = label or favorite.label
        else:
            favorite = FavoriteStation(station_id=station.id, label=label)
            session.add(favorite)
        await session.commit()
        await session.refresh(favorite)
        return favorite

    async def delete_favorite(self, session: AsyncSession, favorite_id: str) -> None:
        favorite = await session.get(FavoriteStation, favorite_id)
        if not favorite:
            raise ValueError("Favorit nicht gefunden.")
        await session.delete(favorite)
        await session.commit()

    async def refresh_favorite_snapshots(self, session: AsyncSession) -> int:
        result = await session.execute(select(FavoriteStation, Station).join(Station))
        rows = result.all()
        station_ids = [station.external_station_id for _, station in rows]
        if not station_ids:
            return 0

        count = 0
        for start in range(0, len(station_ids), 10):
            current = await self.tanker_client.get_prices(station_ids[start : start + 10])
            for _, station in rows:
                values = current["items"].get(station.external_station_id)
                if not values:
                    continue
                count += await self.station_service.save_price_snapshots(
                    session,
                    station,
                    values,
                    observed_at=current["fetched_at"],
                )
                await self.record_price_change(session, station, values, current["fetched_at"])
        await session.commit()
        return count

    async def get_latest_snapshot(self, session: AsyncSession, station_id) -> PriceSnapshot | None:
        result = await session.execute(
            select(PriceSnapshot)
            .where(PriceSnapshot.station_id == station_id)
            .order_by(PriceSnapshot.observed_at.desc())
        )
        return result.scalars().first()

    async def record_price_change(
        self,
        session: AsyncSession,
        station: Station,
        values: dict[str, Any],
        observed_at: datetime,
    ) -> None:
        latest = await session.execute(
            select(PriceChange)
            .where(PriceChange.station_id == station.id)
            .order_by(PriceChange.changed_at.desc())
        )
        last_change = latest.scalars().first()
        normalized = {
            "e5": values.get("e5"),
            "e10": values.get("e10"),
            "diesel": values.get("diesel"),
        }
        if last_change and all(
            (getattr(last_change, fuel) is None and normalized[fuel] in (None, False))
            or (getattr(last_change, fuel) is not None and float(getattr(last_change, fuel)) == float(normalized[fuel]))
            for fuel in ("e5", "e10", "diesel")
            if normalized[fuel] not in (None, False) or getattr(last_change, fuel) is not None
        ):
            return

        session.add(
            PriceChange(
                station_id=station.id,
                e5=Decimal(str(normalized["e5"])) if normalized["e5"] not in (None, False) else None,
                e10=Decimal(str(normalized["e10"])) if normalized["e10"] not in (None, False) else None,
                diesel=Decimal(str(normalized["diesel"])) if normalized["diesel"] not in (None, False) else None,
                changed_at=observed_at,
                source="tankerkoenig",
            )
        )
        await session.flush()
