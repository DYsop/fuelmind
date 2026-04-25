# Datenmodell

FuelMind speichert nicht nur Live-Ergebnisse, sondern baut eine lokale Historie fuer Analyse, Favoriten und Preisalarme auf. Die wichtigsten Tabellen sind unten kurz beschrieben.

## `stations`

Speichert Stammdaten der Tankstellen.

- `id`: interne UUID
- `external_station_id`: externe Tankerkoenig-ID
- `name`, `brand`, `street`, `house_number`, `post_code`, `city`
- `lat`, `lng`
- `location`: Geopunkt fuer PostGIS oder portable Testdarstellung
- `is_active`, `created_at`, `updated_at`

## `price_snapshots`

Speichert beobachtete Preise pro Station, Kraftstofftyp und Zeitpunkt.

Diese Tabelle ist die Grundlage fuer:

- Verlaufsansichten
- Analyse
- Alert-Pruefungen
- heuristische Empfehlungen

## `price_changes`

Speichert komprimierte Preiswechsel und bereitet spaetere Event- oder Exportauswertungen vor.

## `favorite_stations`

Verwaltet lokal markierte Tankstellen mit optionalem Label.

## `alert_rules`

Enthaelt die vom Nutzer definierten Regeln fuer Preisalarme.

Typische Inhalte:

- Standort
- Radius
- Kraftstofftyp
- Preisgrenze
- Aktivierungsstatus
- Benachrichtigungskanal

## `alert_events`

Speichert ausgeloeste Preisalarm-Ereignisse inklusive interner Historie und spaeter moeglichem Lieferstatus.

## `app_settings`

Einfache Key-Value-Tabelle fuer Standardwerte wie Standort, Radius oder Filter.

## Modellidee

Die Modellierung trennt klar zwischen:

- Stammdaten einer Tankstelle
- beobachteten Preisen ueber die Zeit
- nutzerbezogenen Regeln wie Favoriten und Alerts
- globalen App-Einstellungen

Dadurch bleiben Live-Suche, Historie und Personalisierung sauber voneinander getrennt.
