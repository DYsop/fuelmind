# Datenmodell

## Tabellen

### `stations`

- `id`: interne UUID
- `external_station_id`: eindeutige Tankerkönig-ID
- `name`, `brand`, `street`, `house_number`, `post_code`, `city`
- `lat`, `lng`
- `location`: PostGIS-Point bzw. WKT-kompatibler Punkt in Testumgebungen
- `is_active`, `created_at`, `updated_at`

### `price_snapshots`

- ein Datensatz pro Station, Kraftstofftyp und Beobachtungszeitpunkt
- Grundlage fuer Historie, Alerts, Analysen und spaetere Prognosen

### `price_changes`

- komprimierte Preiswechsel-Tabelle mit E5/E10/Diesel pro Zeitpunkt
- vorbereitet fuer spaetere Export- oder Event-Auswertungen

### `favorite_stations`

- lokale Favoritenliste mit optionalem Label

### `alert_rules`

- Suchradius, Kraftstofftyp, Preisgrenze, Benachrichtigungskanal und Aktivierungsstatus

### `alert_events`

- interne Historie ausgelöster Preisalarme inklusive Lieferstatus

### `app_settings`

- einfache Key-Value-Tabelle fuer Standardstandort und Standardfilter

