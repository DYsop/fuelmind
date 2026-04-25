# FuelMind Architektur

## Zielbild

FuelMind ist als lokal betreibbare Benzinpreis-App fuer private Nutzung aufgebaut. Das Projekt trennt klar zwischen Oberflaeche, API, Datenhaltung und Hintergrundjobs, damit der Stack auf NAS-Systemen und Linux-Servern stabil, nachvollziehbar und spaeter erweiterbar bleibt.

## Hauptkomponenten

- `frontend`: React, Vite und TypeScript fuer die private Weboberflaeche
- `backend`: FastAPI fuer API, Fachlogik, Persistenz und Scheduler
- `postgres`: PostgreSQL mit PostGIS fuer Stammdaten, Snapshots und Alerts
- `redis`: Cache fuer externe API-Abfragen und kurze Zwischenspeicherung

## Architekturprinzipien

- standortbezogene API-Nutzung statt deutschlandweiter Massenabfrage
- private-by-default mit lokaler Bereitstellung
- robuste Funktion auch bei eingeschraenkter externer Erreichbarkeit
- klare Trennung zwischen Live-Abfrage, lokaler Historie und Auswertung
- modulare Erweiterbarkeit fuer Benachrichtigungen, CSV-Importe und Prognosen

## Backend-Struktur

- `api/`: REST-Endpunkte pro Fachbereich
- `core/`: Konfiguration, Logging und Sicherheitslogik
- `db/`: Modelle, Session-Handling und Datenbankinitialisierung
- `services/`: Tankerkoenig-Client, Preislogik, Favoriten, Alerts und Analyse
- `scheduler/`: zeitgesteuerte Jobs fuer Synchronisierung und Pruefungen

## Datenfluss

1. Das Frontend sendet Anfragen an das Backend.
2. Das Backend validiert Parameter und liest zuerst vorhandene lokale Daten oder Cache-Eintraege.
3. Nur bei Bedarf wird die externe Tankerkoenig-API angesprochen.
4. Relevante Ergebnisse werden lokal gespeichert und fuer Analyse, Favoriten und Alerts wiederverwendet.
5. Der Scheduler aktualisiert periodisch Favoritenpreise und prueft bestehende Preisalarme.

## Speicherung

In PostgreSQL werden unter anderem diese Informationen gehalten:

- Tankstellen-Stammdaten
- Preis-Snapshots
- Preisveraenderungen
- Favoriten
- Alert-Regeln und Alert-Ereignisse
- App-Standardeinstellungen

Redis wird bewusst nur als Cache genutzt. Die eigentliche Historie liegt in PostgreSQL.

## Scheduler-Rolle

Der Scheduler uebernimmt Hintergrundaufgaben, solange das Backend laeuft:

- Favoriten synchronisieren
- Preisalarme pruefen
- alte Cache-Eintraege bereinigen

Dadurch bleiben die Live-Suche, die lokale Historie und die Alarm-Logik voneinander getrennt.

## Erweiterungspunkte

Die Architektur ist so vorbereitet, dass spaeter ohne grossen Umbau erweitert werden kann:

- externe Benachrichtigungskanaele wie Telegram, `ntfy` oder E-Mail
- CSV-Importe historischer Daten
- weitergehende PostGIS-Auswertungen
- Prognose- oder ML-Module
- Dashboards und Observability-Komponenten

## Annahmen

- FuelMind ist fuer private, lokale Nutzung gedacht.
- Der wichtigste externe Datenlieferant ist die Tankerkoenig-API.
- In Testumgebungen kann Geometrie vereinfacht gespeichert werden, im Compose-Stack ist PostGIS aktiv.
- Externe Dienste koennen ausfallen, ohne dass die gesamte App unbrauchbar wird.
