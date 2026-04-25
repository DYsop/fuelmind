# FuelMind API

Diese Seite gibt einen kompakten Ueberblick ueber die wichtigsten Endpunkte des Backends. Die Beispiele sind bewusst kurz gehalten und dienen als Orientierung fuer Entwicklung, Tests und spaetere Integrationen.

## Health

`GET /api/health`

Beispielantwort:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok",
  "external_api_configured": true
}
```

## Tankstellen

Suche im Umkreis:

`GET /api/stations/nearby?lat=51.45&lng=6.76&radius_km=10&fuel_type=e10&sort=price`

Beispielantwort:

```json
{
  "items": [
    {
      "station_id": "24a381e3-0d72-416d-bfd8-b2f65f6e5802",
      "name": "Beispielstation",
      "brand": "Marke",
      "price": 1.749,
      "fuel_type": "e10",
      "distance_km": 3.2,
      "is_open": true,
      "address": "Musterstrasse 1, 47000 Duisburg",
      "lat": 51.0,
      "lng": 6.0
    }
  ],
  "source": "tankerkoenig",
  "cached": false,
  "fetched_at": "2026-04-21T20:00:00Z"
}
```

Lokale Synchronisierung im Umkreis:

`POST /api/stations/sync-nearby`

Beispielpayload:

```json
{
  "lat": 51.45,
  "lng": 6.76,
  "radius_km": 10,
  "fuel_type": "e10",
  "sort": "price"
}
```

Weitere Endpunkte:

- `GET /api/stations/{station_id}`

## Preise

- `GET /api/prices/current?station_ids=id1,id2,id3`
- `GET /api/prices/history/{station_id}?fuel_type=e10&from_date=2026-04-01T00:00:00Z&to_date=2026-04-21T23:59:59Z`
- `GET /api/prices/cheapest?lat=51.45&lng=6.76&radius_km=10&fuel_type=e10&limit=5`

## Favoriten

- `GET /api/favorites`
- `POST /api/favorites`
- `DELETE /api/favorites/{id}`

Beispielpayload fuer `POST /api/favorites`:

```json
{
  "station_id": "24a381e3-0d72-416d-bfd8-b2f65f6e5802",
  "label": "Arbeitsweg"
}
```

## Alerts

- `GET /api/alerts`
- `POST /api/alerts`
- `PUT /api/alerts/{id}`
- `DELETE /api/alerts/{id}`
- `POST /api/alerts/check-now`

## Analyse und Prognose

- `GET /api/analytics/station/{station_id}?fuel_type=e10&days=7`
- `GET /api/analytics/best-time?lat=51.45&lng=6.76&radius_km=10&fuel_type=e10`
- `GET /api/prediction/recommendation?lat=51.45&lng=6.76&radius_km=10&fuel_type=e10`

## Einstellungen

- `GET /api/settings`
- `PUT /api/settings/defaults`

## Hinweise

- Viele Endpunkte arbeiten mit Koordinaten, Radius und Kraftstofftyp.
- Such- und Preisendpunkte koennen Live-Daten, Cache und lokale Historie kombinieren.
- Fuer Entwicklung und manuelle Tests eignet sich auch [scripts/example_requests.http](../scripts/example_requests.http).
