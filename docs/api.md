# FuelMind API

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

`POST /api/stations/sync-nearby`

```json
{
  "lat": 51.45,
  "lng": 6.76,
  "radius_km": 10,
  "fuel_type": "e10",
  "sort": "price"
}
```

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

## Analytics und Prediction

- `GET /api/analytics/station/{station_id}?fuel_type=e10&days=7`
- `GET /api/analytics/best-time?lat=51.45&lng=6.76&radius_km=10&fuel_type=e10`
- `GET /api/prediction/recommendation?lat=51.45&lng=6.76&radius_km=10&fuel_type=e10`

## Einstellungen

- `GET /api/settings`
- `PUT /api/settings/defaults`
