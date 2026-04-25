# FuelMind

FuelMind ist eine lokal betreibbare Benzinpreis-App fuer private Nutzung. Die Anwendung kombiniert aktuelle Tankerkoenig-Abfragen mit lokaler Historisierung, Favoriten, Preisalarmen, Analysefunktionen und einer Docker-faehigen Architektur fuer NAS-Systeme und Linux-Server.

> Private fuel price app for NAS systems with local history, alerts, analytics and Docker deployment.

## Warum FuelMind?

FuelMind richtet sich an Menschen, die Tankpreise lokal beobachten wollen, ohne ihre Daten oder ihren Workflow an einen fremden Cloud-Dienst abzugeben. Die App laeuft im eigenen Netzwerk, speichert Historie lokal und ist auf self-hosted Setups mit NAS oder Home-Server ausgelegt.

**Highlights**

- self-hosted und Docker-basiert
- lokale Preis-Historie statt reiner Live-Abfrage
- Favoriten, Preisalarme und Analyse in einer Anwendung
- optimiert fuer NAS-Systeme und private Netzwerke

## Was FuelMind kann

- aktuelle Preise fuer E5, E10 und Diesel abrufen
- Tankstellen im Umkreis nach Preis oder Distanz suchen
- Favoriten lokal speichern und regelmaessig aktualisieren
- Preisalarme fuer einen Standort und Suchradius anlegen
- Preis-Snapshots historisieren und spaeter auswerten
- lokale Empfehlungen und guenstige Zeitfenster ableiten
- auf UGREEN, Synology, QNAP oder generischen Linux-Servern laufen

## Architektur

- `frontend`: React, Vite, TypeScript
- `backend`: FastAPI, SQLAlchemy, APScheduler
- `postgres`: PostgreSQL 16 mit PostGIS
- `redis`: Cache fuer API-Abfragen

Mehr Details:

- [Architektur](docs/architecture.md)
- [API](docs/api.md)
- [Datenmodell](docs/data_model.md)
- [Roadmap](docs/roadmap.md)
- [Screenshot-Guide](docs/SCREENSHOTS.md)
- [GitHub-Metadaten und Topics](docs/GITHUB_SETUP.md)

## Voraussetzungen

- Docker Engine mit Docker Compose Plugin
- gueltiger Tankerkoenig-API-Key
- lokales oder privates Netzwerk fuer den Betrieb

## Schnellstart

1. Projekt kopieren oder klonen.
2. `.env.example` nach `.env` kopieren.
3. `TANKERKOENIG_API_KEY` und `POSTGRES_PASSWORD` setzen.
4. Stack starten:

```bash
docker compose up -d
```

Danach ist die Anwendung typischerweise unter diesen Adressen erreichbar:

- Frontend: `http://localhost:3000`
- Backend/OpenAPI: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/health`

## Wichtige `.env`-Werte

Pflicht:

- `TANKERKOENIG_API_KEY`
- `POSTGRES_PASSWORD`

Haeufig angepasst:

- `DEFAULT_LAT`
- `DEFAULT_LNG`
- `DEFAULT_RADIUS_KM=10`
- `DEFAULT_FUEL_TYPE=e10`
- `ENABLE_SCHEDULER=true`
- `FRONTEND_API_BASE_URL=http://localhost:8000/api`
- `ALLOW_PUBLIC_API=false`

Optional:

- `APP_INTERNAL_TOKEN`
- `NOTIFICATION_MODE`
- `SMTP_*`
- `NTFY_TOPIC`
- `TELEGRAM_*`

## Docker-Befehle

```bash
docker compose up -d
docker compose logs -f backend
docker compose down
docker compose down -v
```

Optional:

- `docker compose --profile tools up -d adminer`
- `docker compose --profile observability up -d grafana`

## Betrieb auf dem NAS

Auf dem NAS kannst du das Hilfsskript [fuelmind.sh](fuelmind.sh) nutzen:

```bash
bash fuelmind.sh
bash fuelmind.sh status
bash fuelmind.sh logs
bash fuelmind.sh stop
```

Wenn du auf dem NAS lieber direkt nur `fuelmind` tippen willst:

```bash
bash install-fuelmind-command.sh
export PATH="$HOME/.local/bin:$PATH"
fuelmind
fuelmind status
```

## Windows-Workflow

Das Skript [sync-to-nas.ps1](sync-to-nas.ps1) kopiert den Projektordner nach `Z:\docker\fuelmind`:

```powershell
cd C:\Users\dietm\Documents\Codex\2026-04-21-du-bist-codex-und-arbeitest-als\fuelmind
powershell -ExecutionPolicy Bypass -File .\sync-to-nas.ps1
```

Standardverhalten:

- `.env` wird aus Sicherheitsgruenden nicht automatisch auf das NAS kopiert
- wenn du sie bewusst mitsynchronisieren willst:

```powershell
powershell -ExecutionPolicy Bypass -File .\sync-to-nas.ps1 -IncludeEnvFile
```

Danach auf dem NAS bei Bedarf:

```bash
fuelmind rebuild
```

## Funktionen im Ueberblick

- Dashboard: guenstige Tankstellen, Empfehlung und schneller Ueberblick
- Stationssuche: Umkreissuche, Standortwahl, Favoritenanlage
- Favoriten: lokal gespeicherte Tankstellen und letzte Snapshots
- Preisalarme: Regeln nach Standort, Radius und Preisgrenze
- Analyse: Stundenprofile, Historie und guenstige Zeitfenster
- Einstellungen: Standardstandort, Standardfilter und Scheduler-Status

## Backend-Endpunkte

- `GET /api/health`
- `GET /api/stations/nearby`
- `GET /api/stations/{station_id}`
- `POST /api/stations/sync-nearby`
- `GET /api/prices/current`
- `GET /api/prices/history/{station_id}`
- `GET /api/prices/cheapest`
- `GET /api/favorites`
- `POST /api/favorites`
- `DELETE /api/favorites/{id}`
- `GET /api/alerts`
- `POST /api/alerts`
- `PUT /api/alerts/{id}`
- `DELETE /api/alerts/{id}`
- `POST /api/alerts/check-now`
- `GET /api/analytics/station/{station_id}`
- `GET /api/analytics/best-time`
- `GET /api/prediction/recommendation`
- `GET /api/settings`
- `PUT /api/settings/defaults`

Beispiele stehen in [docs/api.md](docs/api.md) und [scripts/example_requests.http](scripts/example_requests.http).

## Datenmodell

Die wichtigsten Tabellen:

- `stations`
- `price_snapshots`
- `price_changes`
- `favorite_stations`
- `alert_rules`
- `alert_events`
- `app_settings`

Mehr dazu in [docs/data_model.md](docs/data_model.md).

## Scheduler

- `sync_favorites_prices`: alle 10 Minuten
- `check_alerts`: alle 5 Minuten
- `cleanup_old_cache`: taeglich

Der Scheduler kann ueber `ENABLE_SCHEDULER=false` deaktiviert werden.

Wichtig: FuelMind fuehrt keine deutschlandweite Massenabfrage durch. Automatische Jobs arbeiten nur auf Favoriten und expliziten Alert-Radien.

## Analyse und Prognose

FuelMind arbeitet lokal mit historischen Preis-Snapshots und leitet daraus einfache Empfehlungen ab.

Aktuell vorbereitet:

- Stundenprofile pro Tankstelle
- Min/Max/Durchschnittswerte
- guenstige Zeitfenster per Stundenaggregation
- heuristische Empfehlung `tank_now`, `wait` oder `neutral`

Beispiel:

- `tank_now`, wenn der aktuelle Preis unter dem 25%-Quantil der letzten 7 Tage liegt
- `wait`, wenn spaeter historisch guenstigere Zeitfenster auftreten
- `neutral`, wenn die Datenlage uneindeutig ist

## CSV-Import

Das Skript [scripts/import_historical_prices.py](scripts/import_historical_prices.py) ist als Adapterstruktur fuer spaetere historische Datenquellen vorbereitet.

Enthalten sind u. a.:

- `detect_format()`
- `validate_columns()`
- `parse_row()`
- `insert_batch()`

## Rechtliche Hinweise

- FuelMind ist fuer private, lokale Nutzung vorgesehen.
- Die Tankerkoenig-AGB und die Bedingungen der MTS-K sind einzuhalten.
- Die Daten duerfen nicht automatisiert massenhaft abgefragt werden.
- Die Daten duerfen nicht an Mineraloelunternehmen, Tankstellenbetreiber oder fuer diese taetige IT-Dienstleister weitergegeben werden.
- Die bezogenen Datensaetze duerfen nicht als eigene API an Dritte weitergereicht werden.
- Die App ist kein Preissteuerungs- oder Preisoptimierungssystem fuer Tankstellen.
- Nutzerinnen und Nutzer sind selbst fuer die Einhaltung der Nutzungsbedingungen verantwortlich.

## Troubleshooting

- `health` zeigt `database=error`: PostgreSQL-Container, Zugangsdaten und Volumes pruefen
- `redis=error` oder `unavailable`: FuelMind laeuft weiter, aber ohne zentralen Cache
- `503` bei Stationssuche: API-Key, Internetzugang und Tankerkoenig-Verfuegbarkeit pruefen
- Frontend erreicht Backend nicht: `FRONTEND_API_BASE_URL` und Port-Mappings pruefen
- Keine Empfehlungen: zuerst lokale Historie ueber Suche, Favoriten oder Scheduler aufbauen

## Tests

Backend-Tests laufen mit `pytest` und verwenden nur gemockte externe API-Daten:

```bash
cd backend
pytest
```

## Screenshots

<!-- screenshots:start -->

### Desktop

![Dashboard 01](docs/images/screenshots/desktop/Dashboard_01.jpg)
![Dashboard 02](docs/images/screenshots/desktop/Dashboard_02.jpg)
![Stationssuche](docs/images/screenshots/desktop/Stationssuche.jpg)
![Preisalarm](docs/images/screenshots/desktop/Preisalarm.jpg)
![Favoriten](docs/images/screenshots/desktop/Favoriten.jpg)
![Analyse](docs/images/screenshots/desktop/Analyse.jpg)
![Einstellungen](docs/images/screenshots/desktop/Einstellungen.jpg)

<!-- screenshots:end -->

## GitHub-Optimierung

Fuer eine bessere GitHub-Startseite findest du hier vorbereitete Inhalte:

- [Description, Topics und Social-Preview-Hinweise](docs/GITHUB_SETUP.md)
- [Social-Preview-Vorlage](docs/images/branding/social-preview-template.svg)
