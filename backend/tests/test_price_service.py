from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select


@pytest.mark.asyncio
async def test_sync_nearby_stores_stations_and_snapshots(configured_app, db_session):
    app, _ = configured_app
    from app.db.models import PriceSnapshot, Station

    async def fake_search_nearby(**_kwargs):
        return {
            "items": [
                {
                    "station_id": "station-a",
                    "name": "Fuel A",
                    "brand": "Fuel",
                    "price": 1.699,
                    "fuel_type": "e10",
                    "distance_km": 1.1,
                    "is_open": True,
                    "address": "Testweg 1, 12345 Berlin",
                    "lat": 52.5,
                    "lng": 13.4,
                    "e5": 1.759,
                    "e10": 1.699,
                    "diesel": 1.589,
                    "street": "Testweg",
                    "house_number": "1",
                    "post_code": "12345",
                    "city": "Berlin",
                }
            ],
            "source": "tankerkoenig",
            "cached": False,
            "fetched_at": datetime.now(UTC),
        }

    app.state.station_service.search_nearby = fake_search_nearby
    result = await app.state.station_service.sync_nearby(
        db_session,
        lat=52.5,
        lng=13.4,
        radius_km=10,
        fuel_type="e10",
        sort="price",
    )
    assert result["synced_stations"] == 1

    stations = (await db_session.execute(select(Station))).scalars().all()
    snapshots = (await db_session.execute(select(PriceSnapshot))).scalars().all()
    assert len(stations) == 1
    assert len(snapshots) == 3


@pytest.mark.asyncio
async def test_analytics_and_recommendation_return_values(configured_app, db_session):
    app, _ = configured_app
    from app.db.models import PriceSnapshot, Station

    async def fake_search_nearby(**_kwargs):
        return {
            "items": [
                {
                    "station_id": "station-b",
                    "name": "Fuel B",
                    "brand": "Fuel",
                    "price": 1.555,
                    "fuel_type": "e10",
                    "distance_km": 0.8,
                    "is_open": True,
                    "address": "Preisweg 2, 12345 Berlin",
                    "lat": 52.5,
                    "lng": 13.4,
                    "e5": 1.615,
                    "e10": 1.555,
                    "diesel": 1.499,
                    "street": "Preisweg",
                    "house_number": "2",
                    "post_code": "12345",
                    "city": "Berlin",
                }
            ],
            "source": "tankerkoenig",
            "cached": False,
            "fetched_at": datetime.now(UTC),
        }

    app.state.station_service.search_nearby = fake_search_nearby
    await app.state.station_service.sync_nearby(
        db_session,
        lat=52.5,
        lng=13.4,
        radius_km=10,
        fuel_type="e10",
        sort="price",
    )

    station = (await db_session.execute(select(Station))).scalars().first()
    for hours_back, price in enumerate([1.60, 1.59, 1.58, 1.57, 1.56, 1.55, 1.54, 1.53], start=1):
        db_session.add(
            PriceSnapshot(
                station_id=station.id,
                fuel_type="e10",
                price=price,
                is_open=True,
                observed_at=datetime.now(UTC) - timedelta(hours=hours_back),
                source="test",
            )
        )
    await db_session.commit()

    analytics = await app.state.analytics_service.station_analytics(
        db_session,
        station_id="station-b",
        fuel_type="e10",
        days=7,
    )
    recommendation = await app.state.prediction_service.get_recommendation(
        db_session,
        lat=52.5,
        lng=13.4,
        radius_km=10,
        fuel_type="e10",
    )
    assert analytics["minimum_price"] <= analytics["maximum_price"]
    assert analytics["average_price"] > 0
    assert recommendation["recommendation"] in {"tank_now", "wait", "neutral"}
