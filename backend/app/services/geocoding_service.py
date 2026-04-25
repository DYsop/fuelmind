from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import httpx
from redis.asyncio import Redis

from app.core.config import Settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class GeocodingError(Exception):
    """Base exception for geocoding lookups."""


class GeocodingUnavailableError(GeocodingError):
    """Raised when the upstream geocoding service is unavailable."""


class GeocodingValidationError(GeocodingError):
    """Raised when the upstream geocoding service returns invalid data."""


class GeocodingService:
    def __init__(self, settings: Settings, redis_client: Redis | None = None) -> None:
        self.settings = settings
        self.redis = redis_client
        self.client = httpx.AsyncClient(
            base_url=self.settings.geocoding_base_url.rstrip("/") + "/",
            timeout=self.settings.geocoding_timeout_seconds,
            headers={
                "User-Agent": self.settings.geocoding_user_agent,
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def search(self, query: str, *, limit: int | None = None) -> dict[str, Any]:
        normalized_query = query.strip()
        if len(normalized_query) < 2:
            raise GeocodingValidationError("Bitte mindestens zwei Zeichen fuer die Standortsuche eingeben.")

        params: dict[str, Any] = {
            "q": normalized_query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit or self.settings.geocoding_result_limit,
        }
        if self.settings.geocoding_country_codes:
            params["countrycodes"] = self.settings.geocoding_country_codes

        payload, cached = await self._request_json("search", params=params, ttl=3600 * 24)
        if not isinstance(payload, list):
            raise GeocodingValidationError("Ungueltige Standortantwort erhalten.")

        return {
            "items": [self._map_item(item) for item in payload],
            "source": "nominatim",
            "cached": cached,
            "fetched_at": datetime.now(UTC),
        }

    async def _request_json(self, endpoint: str, *, params: dict[str, Any], ttl: int) -> tuple[Any, bool]:
        cache_key = self._build_cache_key(endpoint, params)
        cached_payload = await self._cache_get(cache_key)
        if cached_payload is not None:
            return cached_payload, True

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise GeocodingUnavailableError(
                "Standortsuche ist momentan nicht erreichbar. Bitte spaeter erneut versuchen."
            ) from exc

        await self._cache_set(cache_key, payload, ttl)
        return payload, False

    def _build_cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        normalized = json.dumps({"endpoint": endpoint, "params": params}, sort_keys=True)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"fuelmind:geocoding:{digest}"

    async def _cache_get(self, key: str) -> Any | None:
        if not self.redis:
            return None
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            logger.warning("Geocoding-Cache nicht erreichbar, fahre ohne Cache fort.")
            return None

    async def _cache_set(self, key: str, payload: Any, ttl: int) -> None:
        if not self.redis:
            return
        try:
            await self.redis.set(key, json.dumps(payload), ex=ttl)
        except Exception:
            logger.warning("Geocoding-Cache konnte nicht beschrieben werden.")

    def _map_item(self, item: dict[str, Any]) -> dict[str, Any]:
        display_name = item.get("display_name")
        lat = item.get("lat")
        lng = item.get("lon")
        if not display_name or lat is None or lng is None:
            raise GeocodingValidationError("Standortsuche hat unvollstaendige Daten geliefert.")

        address = item.get("address", {}) if isinstance(item.get("address"), dict) else {}
        return {
            "label": display_name,
            "lat": float(lat),
            "lng": float(lng),
            "city": address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality"),
            "post_code": address.get("postcode"),
            "street": address.get("road") or address.get("pedestrian"),
            "house_number": address.get("house_number"),
        }
