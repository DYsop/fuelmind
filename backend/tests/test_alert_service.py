from __future__ import annotations

from datetime import UTC, datetime

import pytest


@pytest.mark.asyncio
async def test_alert_rule_triggers_when_price_below_threshold(configured_app, db_session):
    app, _ = configured_app
    await app.state.alert_service.create_rule(
        db_session,
        {
            "name": "Guenstig",
            "fuel_type": "e10",
            "max_price": 1.7,
            "lat": 52.5,
            "lng": 13.4,
            "radius_km": 10,
            "enabled": True,
            "notification_channel": "none",
        },
    )

    async def fake_search_nearby(**_kwargs):
        return {
            "items": [
                {
                    "station_id": "station-alert",
                    "name": "Alert Station",
                    "brand": "Fuel",
                    "price": 1.659,
                    "fuel_type": "e10",
                    "distance_km": 1.0,
                    "is_open": True,
                    "address": "Alertweg 3, 12345 Berlin",
                    "lat": 52.5,
                    "lng": 13.4,
                    "e5": 1.719,
                    "e10": 1.659,
                    "diesel": 1.549,
                    "street": "Alertweg",
                    "house_number": "3",
                    "post_code": "12345",
                    "city": "Berlin",
                }
            ],
            "source": "tankerkoenig",
            "cached": False,
            "fetched_at": datetime.now(UTC),
        }

    app.state.station_service.search_nearby = fake_search_nearby
    result = await app.state.alert_service.check_alerts(db_session)
    assert result["events_created"] == 1


@pytest.mark.asyncio
async def test_alert_rule_does_not_trigger_when_price_too_high(configured_app, db_session):
    app, _ = configured_app
    await app.state.alert_service.create_rule(
        db_session,
        {
            "name": "Zu teuer",
            "fuel_type": "diesel",
            "max_price": 1.4,
            "lat": 52.5,
            "lng": 13.4,
            "radius_km": 10,
            "enabled": True,
            "notification_channel": "none",
        },
    )

    async def fake_search_nearby(**_kwargs):
        return {
            "items": [
                {
                    "station_id": "station-no-alert",
                    "name": "No Alert Station",
                    "brand": "Fuel",
                    "price": 1.559,
                    "fuel_type": "diesel",
                    "distance_km": 1.0,
                    "is_open": True,
                    "address": "Teuerweg 4, 12345 Berlin",
                    "lat": 52.5,
                    "lng": 13.4,
                    "e5": 1.719,
                    "e10": 1.659,
                    "diesel": 1.559,
                    "street": "Teuerweg",
                    "house_number": "4",
                    "post_code": "12345",
                    "city": "Berlin",
                }
            ],
            "source": "tankerkoenig",
            "cached": False,
            "fetched_at": datetime.now(UTC),
        }

    app.state.station_service.search_nearby = fake_search_nearby
    result = await app.state.alert_service.check_alerts(db_session)
    assert result["events_created"] == 0

