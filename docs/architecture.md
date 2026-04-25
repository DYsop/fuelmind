# FuelMind Architektur

## Zielbild

FuelMind ist als lokal betreibbare, private Benzinpreis-Intelligence-App fuer NAS-Systeme und Linux-Server aufgebaut. Das Projekt trennt klar zwischen:

- `frontend`: React/Vite/TypeScript fuer die private Weboberflaeche
- `backend`: FastAPI fuer API, Persistenz, Scheduler und Fachlogik
- `postgres`: lokale Speicherung von Stammdaten, Snapshots, Preisveraenderungen und Alert-Historie
- `redis`: Cache fuer Tankerkönig-Anfragen und leichte Entkopplung der Zugriffe

## Architekturprinzipien

- Gezielte API-Nutzung: keine deutschlandweite Massenabfrage, nur standortbezogene Umkreissuchen, Favoriten und Alert-Radien
- Graceful Degradation: FuelMind startet auch ohne erreichbare externe API oder Redis
- Private-by-default: `ALLOW_PUBLIC_API=false` und optionaler `APP_INTERNAL_TOKEN`
- Erweiterbarkeit: Analytics, historische CSV-Importe, Benachrichtigungen und ML-Prognosen sind modular vorbereitet

## Backend-Module

- `api/`: REST-Endpunkte pro Fachbereich
- `core/`: Konfiguration, Logging, Netz- und Token-Schutz
- `db/`: SQLAlchemy-Modelle, Session-Handling, Alembic-Basis
- `services/`: Tankerkönig-Client, Stationen, Preise, Alerts, Analytics, Prognosen
- `scheduler/`: APScheduler-Jobs fuer Favoriten und Alert-Pruefungen

## Datenfluss

1. Frontend fragt Backend-Endpunkte ab.
2. Backend nutzt den Tankerkönig-Client nur bedarfsorientiert.
3. Responses werden validiert, gemappt, optional gecacht und dann in PostgreSQL persistiert.
4. Analytics und Heuristiken arbeiten primaer auf lokalen historischen Snapshots.

## Annahmen

- Fuer Tests und portable Entwicklung kann das `location`-Feld in SQLite als WKT-String gespeichert werden.
- In PostgreSQL/PostGIS wird das Feld als `POINT`-Geometrie angelegt.
- Die genaue Tankerkönig-Response-Struktur ist in `services/tankerkoenig_client.py` gekapselt und damit leicht anpassbar.

