from __future__ import annotations

import pytest
from httpx import MockTransport, Response

from app.core.config import get_settings
from app.services.tankerkoenig_client import TankerkoenigClient, TankerkoenigUnavailableError


@pytest.mark.asyncio
async def test_tankerkoenig_client_maps_nearby_response(monkeypatch):
    monkeypatch.setenv("TANKERKOENIG_API_KEY", "demo")
    get_settings.cache_clear()
    settings = get_settings()

    def handler(request):
        assert request.url.path.endswith("/list.php")
        return Response(
            200,
            json={
                "ok": True,
                "stations": [
                    {
                        "id": "station-1",
                        "name": "Test Station",
                        "brand": "Brand",
                        "street": "Hauptstrasse",
                        "houseNumber": "1",
                        "postCode": 12345,
                        "place": "Berlin",
                        "lat": 52.5,
                        "lng": 13.4,
                        "dist": 1.2,
                        "price": 1.699,
                        "isOpen": True,
                    }
                ],
            },
        )

    client = TankerkoenigClient(settings)
    client.client = client.client.__class__(
        base_url=settings.tankerkoenig_base_url.rstrip("/") + "/",
        timeout=settings.tankerkoenig_timeout_seconds,
        transport=MockTransport(handler),
    )
    payload = await client.get_nearby_stations(lat=52.5, lng=13.4, radius_km=5, fuel_type="e10", sort="price")
    assert payload["items"][0]["station_id"] == "station-1"
    assert payload["items"][0]["price"] == 1.699
    await client.close()


@pytest.mark.asyncio
async def test_tankerkoenig_client_handles_api_failure(monkeypatch):
    monkeypatch.setenv("TANKERKOENIG_API_KEY", "demo")
    monkeypatch.setenv("TANKERKOENIG_MAX_RETRIES", "1")
    get_settings.cache_clear()
    settings = get_settings()

    def handler(_request):
        return Response(503, json={"ok": False, "message": "temporarily unavailable"})

    client = TankerkoenigClient(settings)
    client.client = client.client.__class__(
        base_url=settings.tankerkoenig_base_url.rstrip("/") + "/",
        timeout=settings.tankerkoenig_timeout_seconds,
        transport=MockTransport(handler),
    )
    with pytest.raises(TankerkoenigUnavailableError):
        await client.get_nearby_stations(lat=52.5, lng=13.4, radius_km=5, fuel_type="e10", sort="price")
    await client.close()

