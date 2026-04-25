from __future__ import annotations

import hashlib
import json
import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx
from redis.asyncio import Redis

from app.core.config import Settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class TankerkoenigError(Exception):
    """Base exception for Tankerkönig client errors."""


class TankerkoenigConfigurationError(TankerkoenigError):
    """Raised when the client is not configured correctly."""


class TankerkoenigUnavailableError(TankerkoenigError):
    """Raised when the remote API is unavailable."""


class TankerkoenigRateLimitError(TankerkoenigError):
    """Raised when the API rate limit appears to be exceeded."""


class TankerkoenigValidationError(TankerkoenigError):
    """Raised when the API returns an unexpected payload."""


class TankerkoenigClient:
    def __init__(self, settings: Settings, redis_client: Redis | None = None) -> None:
        self.settings = settings
        self.redis = redis_client
        self.client = httpx.AsyncClient(
            base_url=self.settings.tankerkoenig_base_url.rstrip("/") + "/",
            timeout=self.settings.tankerkoenig_timeout_seconds,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def get_nearby_stations(
        self,
        *,
        lat: float,
        lng: float,
        radius_km: float,
        fuel_type: str,
        sort: str,
    ) -> dict[str, Any]:
        api_sort = "dist" if sort == "distance" else sort
        params = {
            "lat": lat,
            "lng": lng,
            "rad": radius_km,
            "type": fuel_type,
            "sort": api_sort,
        }
        payload = await self._request_json(
            "list.php",
            params=params,
            ttl=self.settings.cache_ttl_nearby_seconds,
        )
        stations = payload.get("stations")
        if not isinstance(stations, list):
            raise TankerkoenigValidationError("Ungueltige Stationsliste von Tankerkönig erhalten.")
        return {
            "items": [self._map_nearby_station(item, fuel_type) for item in stations],
            "source": "tankerkoenig",
            "cached": payload.get("_cached", False),
            "fetched_at": datetime.now(UTC),
        }

    async def get_station_detail(self, station_id: str) -> dict[str, Any]:
        payload = await self._request_json(
            "detail.php",
            params={"id": station_id},
            ttl=self.settings.cache_ttl_detail_seconds,
        )
        station = payload.get("station")
        if not isinstance(station, dict):
            raise TankerkoenigValidationError("Ungueltige Detailantwort von Tankerkönig erhalten.")
        return self._map_station_detail(station)

    async def get_prices(self, station_ids: list[str]) -> dict[str, Any]:
        payload = await self._request_json(
            "prices.php",
            params={"ids": ",".join(station_ids)},
            ttl=self.settings.cache_ttl_prices_seconds,
        )
        prices = payload.get("prices")
        if not isinstance(prices, dict):
            raise TankerkoenigValidationError("Ungueltige Preisantwort von Tankerkönig erhalten.")
        return {
            "items": {station_id: self._map_price_item(item) for station_id, item in prices.items()},
            "source": "tankerkoenig",
            "cached": payload.get("_cached", False),
            "fetched_at": datetime.now(UTC),
        }

    async def _request_json(self, endpoint: str, *, params: dict[str, Any], ttl: int) -> dict[str, Any]:
        if not self.settings.tankerkoenig_api_key:
            raise TankerkoenigConfigurationError("TANKERKOENIG_API_KEY ist nicht gesetzt.")

        cache_key = self._build_cache_key(endpoint, params)
        cached_payload = await self._cache_get(cache_key)
        if cached_payload:
            cached_payload["_cached"] = True
            return cached_payload

        request_params = {**params, "apikey": self.settings.tankerkoenig_api_key}
        last_exception: Exception | None = None

        for attempt in range(1, self.settings.tankerkoenig_max_retries + 1):
            try:
                logger.info(
                    "Tankerkönig Anfrage gestartet",
                    extra={"event": "external_api_request", "status": endpoint},
                )
                response = await self.client.get(endpoint, params=request_params)
                if response.status_code == 429:
                    raise TankerkoenigRateLimitError("Tankerkönig Rate-Limit erreicht.")
                response.raise_for_status()
                payload = response.json()
                if not payload.get("ok", False):
                    message = str(payload.get("message", "unbekannter API-Fehler"))
                    if "rate" in message.lower():
                        raise TankerkoenigRateLimitError(message)
                    raise TankerkoenigUnavailableError(message)
                await self._cache_set(cache_key, payload, ttl)
                payload["_cached"] = False
                return payload
            except TankerkoenigError:
                raise
            except httpx.HTTPStatusError as exc:
                last_exception = exc
            except httpx.HTTPError as exc:
                last_exception = exc

            if attempt < self.settings.tankerkoenig_max_retries:
                await asyncio.sleep(min(2**attempt, 5))

        raise TankerkoenigUnavailableError(
            f"Tankerkönig API ist momentan nicht erreichbar: {last_exception}"
        ) from last_exception

    def _build_cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        normalized = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"fuelmind:tankerkoenig:{digest}"

    async def _cache_get(self, key: str) -> dict[str, Any] | None:
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            if not value:
                logger.info("Cache miss", extra={"event": "cache_miss", "cache_key": key})
                return None
            logger.info("Cache hit", extra={"event": "cache_hit", "cache_key": key})
            return json.loads(value)
        except Exception:
            logger.warning("Redis Cache nicht erreichbar, fahre ohne Cache fort.")
            return None

    async def _cache_set(self, key: str, payload: dict[str, Any], ttl: int) -> None:
        if not self.redis:
            return
        try:
            await self.redis.set(key, json.dumps(payload), ex=ttl)
        except Exception:
            logger.warning("Redis Cache konnte nicht beschrieben werden.")

    def _map_nearby_station(self, item: dict[str, Any], fuel_type: str) -> dict[str, Any]:
        station_id = item.get("id")
        if not station_id:
            raise TankerkoenigValidationError("Tankstelle ohne ID erhalten.")
        address = self._compose_address(item)
        if fuel_type == "all":
            price = None
        elif fuel_type == "e5":
            price = item.get("price") or item.get("e5")
        elif fuel_type == "e10":
            price = item.get("price") or item.get("e10")
        else:
            price = item.get("price") or item.get("diesel")
        return {
            "station_id": station_id,
            "name": item.get("name", "Unbekannte Tankstelle"),
            "brand": item.get("brand"),
            "price": price,
            "fuel_type": fuel_type,
            "distance_km": item.get("dist"),
            "is_open": item.get("isOpen"),
            "address": address,
            "lat": item.get("lat"),
            "lng": item.get("lng"),
            "e5": item.get("e5"),
            "e10": item.get("e10"),
            "diesel": item.get("diesel"),
            "street": item.get("street"),
            "house_number": item.get("houseNumber"),
            "post_code": str(item.get("postCode")) if item.get("postCode") is not None else None,
            "city": item.get("place"),
        }

    def _map_station_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "station_id": item.get("id"),
            "name": item.get("name", "Unbekannte Tankstelle"),
            "brand": item.get("brand"),
            "address": self._compose_address(item),
            "lat": item.get("lat"),
            "lng": item.get("lng"),
            "is_open": item.get("isOpen"),
            "prices": {
                "e5": item.get("e5"),
                "e10": item.get("e10"),
                "diesel": item.get("diesel"),
            },
            "opening_times": item.get("openingTimes", []),
            "overrides": item.get("overrides", []),
            "street": item.get("street"),
            "house_number": item.get("houseNumber"),
            "post_code": str(item.get("postCode")) if item.get("postCode") is not None else None,
            "city": item.get("place"),
        }

    def _map_price_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": item.get("status"),
            "is_open": item.get("status") == "open",
            "e5": item.get("e5"),
            "e10": item.get("e10"),
            "diesel": item.get("diesel"),
        }

    @staticmethod
    def _compose_address(item: dict[str, Any]) -> str:
        parts = [
            " ".join(part for part in [item.get("street"), item.get("houseNumber")] if part),
            " ".join(part for part in [str(item.get("postCode")) if item.get("postCode") else None, item.get("place")] if part),
        ]
        return ", ".join(part for part in parts if part)
