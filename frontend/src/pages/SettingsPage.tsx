import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { LocationSearchItem, SettingsResponse } from "../api/types";
import { LocationSearchBox } from "../components/LocationSearchBox";
import { SectionCard } from "../components/SectionCard";

function hasCoordinates(lat: string, lng: string) {
  return lat.trim().length > 0 && lng.trim().length > 0;
}

export function SettingsPage() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [form, setForm] = useState({
    default_lat: "",
    default_lng: "",
    default_radius_km: "10",
    default_fuel_type: "e10",
  });
  const [locationQuery, setLocationQuery] = useState("");
  const [locationResults, setLocationResults] = useState<LocationSearchItem[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<LocationSearchItem | null>(null);
  const [locationSearchPending, setLocationSearchPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.settings()
      .then((data) => {
        setSettings(data);
        setForm({
          default_lat: data.default_lat?.toString() ?? "",
          default_lng: data.default_lng?.toString() ?? "",
          default_radius_km: data.default_radius_km.toString(),
          default_fuel_type: data.default_fuel_type,
        });
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  function applyLocation(location: LocationSearchItem) {
    setSelectedLocation(location);
    setLocationQuery(location.label);
    setLocationResults([]);
    setForm((current) => ({
      ...current,
      default_lat: location.lat.toFixed(5),
      default_lng: location.lng.toFixed(5),
    }));
  }

  function applyCoordinates(lat: number, lng: number) {
    setSelectedLocation({
      label: `Kartenpunkt ${lat.toFixed(5)}, ${lng.toFixed(5)}`,
      lat,
      lng,
    });
    setLocationQuery("");
    setLocationResults([]);
    setForm((current) => ({
      ...current,
      default_lat: lat.toFixed(5),
      default_lng: lng.toFixed(5),
    }));
  }

  async function lookupLocations(query = locationQuery) {
    const normalized = query.trim();
    if (normalized.length < 2) {
      throw new Error("Bitte mindestens zwei Zeichen fuer die Standortsuche eingeben.");
    }

    setLocationSearchPending(true);
    try {
      const response = await api.searchLocations(normalized);
      setLocationResults(response.items);
      if (!response.items.length) {
        throw new Error("Kein passender Standort gefunden.");
      }
      return response.items;
    } finally {
      setLocationSearchPending(false);
    }
  }

  async function resolveLocationForSave() {
    if (selectedLocation) {
      return selectedLocation;
    }
    if (locationQuery.trim()) {
      const items = await lookupLocations(locationQuery);
      const bestMatch = items[0];
      applyLocation(bestMatch);
      return bestMatch;
    }
    if (!hasCoordinates(form.default_lat, form.default_lng)) {
      throw new Error("Bitte zuerst einen Ort, eine PLZ oder manuelle Koordinaten hinterlegen.");
    }
    return null;
  }

  async function save() {
    setError(null);
    setMessage(null);
    try {
      const resolvedLocation = await resolveLocationForSave();
      await api.updateSettings({
        default_lat: resolvedLocation?.lat ?? (form.default_lat ? Number(form.default_lat) : null),
        default_lng: resolvedLocation?.lng ?? (form.default_lng ? Number(form.default_lng) : null),
        default_radius_km: Number(form.default_radius_km),
        default_fuel_type: form.default_fuel_type,
      });
      const refreshed = await api.settings();
      setSettings(refreshed);
      setForm({
        default_lat: refreshed.default_lat?.toString() ?? "",
        default_lng: refreshed.default_lng?.toString() ?? "",
        default_radius_km: refreshed.default_radius_km.toString(),
        default_fuel_type: refreshed.default_fuel_type,
      });
      setMessage(
        resolvedLocation
          ? `Standardstandort gespeichert: ${resolvedLocation.label}`
          : "Standardwerte wurden gespeichert.",
      );
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <SectionCard title="Systemstatus" subtitle="Backend-Konfiguration und Betriebsmodus fuer den lokalen Einsatz.">
        {settings ? (
          <div className="stats-grid">
            <div className="card metric-pill">
              <span>Externe API</span>
              <strong>{settings.external_api_configured ? "Konfiguriert" : "Nicht gesetzt"}</strong>
            </div>
            <div className="card metric-pill">
              <span>Scheduler</span>
              <strong>{settings.scheduler_enabled ? "Aktiv" : "Deaktiviert"}</strong>
            </div>
            <div className="card metric-pill">
              <span>API-Freigabe</span>
              <strong>{settings.allow_public_api ? "Oeffentlich" : "Privat"}</strong>
            </div>
            <div className="card metric-pill">
              <span>Benachrichtigung</span>
              <strong>{settings.notification_mode}</strong>
            </div>
          </div>
        ) : (
          <p>Einstellungen werden geladen...</p>
        )}
      </SectionCard>

      <SectionCard title="Standardstandort" subtitle="Diese Werte verwendet die App automatisch in Dashboard, Suche und Analyse.">
        <LocationSearchBox
          label="Heimatadresse, Ort oder PLZ"
          query={locationQuery}
          onQueryChange={(value) => {
            setLocationQuery(value);
            setSelectedLocation(null);
          }}
          onSearch={async () => {
            setError(null);
            try {
              const items = await lookupLocations();
              applyLocation(items[0]);
              setMessage(`Adresse uebernommen: ${items[0].label}`);
            } catch (err) {
              setError((err as Error).message);
            }
          }}
          searching={locationSearchPending}
          results={locationResults}
          onSelect={(item) => {
            applyLocation(item);
            setMessage(`Adresse uebernommen: ${item.label}`);
          }}
          helperText="Wenn du hier einmal deinen Wohnort, deine PLZ oder deine Strasse hinterlegst, nutzt FuelMind diese Position spaeter automatisch."
          lat={form.default_lat ? Number(form.default_lat) : 51.45}
          lng={form.default_lng ? Number(form.default_lng) : 6.76}
          onMapSelect={(lat, lng) => {
            applyCoordinates(lat, lng);
            setMessage(`Adresse ueber Karte gesetzt: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
          }}
          mapHint="Oder setze deinen Standardstandort direkt durch einen Klick in die Karte."
        />

        {selectedLocation ? <p className="success-text">Aktueller Standardstandort: {selectedLocation.label}</p> : null}

        <div className="filters search-grid compact-grid">
          <label>
            Radius
            <input value={form.default_radius_km} onChange={(event) => setForm({ ...form, default_radius_km: event.target.value })} />
          </label>
          <label>
            Standardkraftstoff
            <select value={form.default_fuel_type} onChange={(event) => setForm({ ...form, default_fuel_type: event.target.value })}>
              <option value="e5">E5</option>
              <option value="e10">E10</option>
              <option value="diesel">Diesel</option>
            </select>
          </label>
        </div>

        <details className="advanced-panel">
          <summary>Koordinaten manuell bearbeiten</summary>
          <div className="filters search-grid">
            <label>
              Breitengrad
              <input value={form.default_lat} onChange={(event) => setForm({ ...form, default_lat: event.target.value })} />
            </label>
            <label>
              Laengengrad
              <input value={form.default_lng} onChange={(event) => setForm({ ...form, default_lng: event.target.value })} />
            </label>
          </div>
        </details>

        <div className="inline-actions">
          <button className="primary-button" onClick={save}>Speichern</button>
        </div>
        {message ? <p className="success-text">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </SectionCard>

      <SectionCard title="Rechtliche Hinweise" subtitle="Wichtige Grenzen fuer die private Nutzung.">
        <p>
          {settings?.legal_note ??
            "FuelMind ist fuer private Nutzung vorgesehen. Massendatenabfragen und die Weitergabe von Datensaetzen an Dritte sind unzulaessig."}
        </p>
      </SectionCard>
    </>
  );
}
