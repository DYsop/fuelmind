import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { AlertEvent, AlertRule, LocationSearchItem } from "../api/types";
import { LocationSearchBox } from "../components/LocationSearchBox";
import { SectionCard } from "../components/SectionCard";

const initialForm = {
  name: "Mein Preisalarm",
  fuel_type: "e10",
  max_price: "1.699",
  lat: "51.4500",
  lng: "6.7600",
  radius_km: "10",
  enabled: true,
  notification_channel: "none",
};

function hasCoordinates(lat: string, lng: string) {
  return lat.trim().length > 0 && lng.trim().length > 0;
}

function parseLocaleNumber(value: string) {
  return Number(value.replace(",", "."));
}

export function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [form, setForm] = useState(initialForm);
  const [locationQuery, setLocationQuery] = useState("");
  const [locationResults, setLocationResults] = useState<LocationSearchItem[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<LocationSearchItem | null>(null);
  const [locationSearchPending, setLocationSearchPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function loadAlerts() {
    try {
      const data = await api.alerts();
      setRules(data.rules);
      setEvents(data.events);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    void loadAlerts();
    api.settings()
      .then((settings) => {
        setForm((current) => ({
          ...current,
          lat: settings.default_lat?.toString() ?? current.lat,
          lng: settings.default_lng?.toString() ?? current.lng,
          radius_km: settings.default_radius_km.toString(),
          fuel_type: settings.default_fuel_type,
        }));
      })
      .catch(() => undefined);
  }, []);

  function applyLocation(location: LocationSearchItem) {
    setSelectedLocation(location);
    setLocationQuery(location.label);
    setLocationResults([]);
    setForm((current) => ({
      ...current,
      lat: location.lat.toFixed(5),
      lng: location.lng.toFixed(5),
    }));
  }

  function applyCoordinates(lat: number, lng: number) {
    applyLocation({
      label: `Kartenpunkt ${lat.toFixed(5)}, ${lng.toFixed(5)}`,
      lat,
      lng,
    });
  }

  async function lookupLocations(query = locationQuery) {
    const normalized = query.trim();
    if (normalized.length < 2) {
      throw new Error("Bitte mindestens zwei Zeichen fuer Ort, PLZ oder Strasse eingeben.");
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

  async function ensureResolvedLocation() {
    if (selectedLocation) {
      return selectedLocation;
    }
    if (locationQuery.trim()) {
      const items = await lookupLocations(locationQuery);
      const bestMatch = items[0];
      applyLocation(bestMatch);
      return bestMatch;
    }
    if (!hasCoordinates(form.lat, form.lng)) {
      throw new Error("Bitte zuerst einen Ort, eine PLZ oder einen Kartenpunkt waehlen.");
    }
    return null;
  }

  async function createAlert() {
    setError(null);
    try {
      const resolvedLocation = await ensureResolvedLocation();
      await api.createAlert({
        ...form,
        max_price: parseLocaleNumber(form.max_price),
        lat: resolvedLocation?.lat ?? Number(form.lat),
        lng: resolvedLocation?.lng ?? Number(form.lng),
        radius_km: parseLocaleNumber(form.radius_km),
      });
      setStatus(
        resolvedLocation
          ? `Preisalarm fuer ${resolvedLocation.label} wurde angelegt.`
          : "Preisalarm wurde angelegt.",
      );
      await loadAlerts();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function deleteAlert(id: string) {
    try {
      await api.deleteAlert(id);
      await loadAlerts();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function checkNow() {
    try {
      const result = await api.checkAlerts();
      setStatus(`${result.events_created} Alert-Events erzeugt.`);
      await loadAlerts();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <SectionCard
        title="Preisalarme"
        subtitle="Lege Alert-Regeln ueber Ort, Karte und Preisgrenze an statt ueber reine Koordinaten."
        action={<button className="secondary-button" onClick={checkNow}>Jetzt pruefen</button>}
      >
        <LocationSearchBox
          label="Standort fuer den Alarm"
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
              setStatus(`Alarm-Standort vorbereitet: ${items[0].label}`);
            } catch (err) {
              setError((err as Error).message);
            }
          }}
          searching={locationSearchPending}
          results={locationResults}
          onSelect={(item) => {
            applyLocation(item);
            setStatus(`Alarm-Standort vorbereitet: ${item.label}`);
          }}
          helperText="Wahlweise Ort, PLZ oder Strasse suchen oder den Mittelpunkt direkt in der Karte anklicken."
          lat={Number(form.lat)}
          lng={Number(form.lng)}
          onMapSelect={(lat, lng) => {
            applyCoordinates(lat, lng);
            setStatus(`Alarm-Standort per Karte gesetzt: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
          }}
          mapHint="Der Alarm prueft Tankstellen im Umkreis des markierten Punkts."
        />

        {selectedLocation ? <p className="success-text">Aktiver Alarm-Standort: {selectedLocation.label}</p> : null}

        <div className="filters search-grid compact-grid">
          <label>
            Name
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
          </label>
          <label>
            Kraftstoff
            <select value={form.fuel_type} onChange={(event) => setForm({ ...form, fuel_type: event.target.value })}>
              <option value="e5">E5</option>
              <option value="e10">E10</option>
              <option value="diesel">Diesel</option>
            </select>
          </label>
          <label>
            Maximalpreis
            <input value={form.max_price} onChange={(event) => setForm({ ...form, max_price: event.target.value })} placeholder="z. B. 1,95 oder 1.95" />
          </label>
          <label>
            Radius
            <input value={form.radius_km} onChange={(event) => setForm({ ...form, radius_km: event.target.value })} />
          </label>
        </div>

        <details className="advanced-panel">
          <summary>Koordinaten manuell bearbeiten</summary>
          <div className="filters search-grid">
            <label>
              Breitengrad
              <input value={form.lat} onChange={(event) => setForm({ ...form, lat: event.target.value })} />
            </label>
            <label>
              Laengengrad
              <input value={form.lng} onChange={(event) => setForm({ ...form, lng: event.target.value })} />
            </label>
          </div>
        </details>

        <div className="inline-actions">
          <button className="primary-button" onClick={createAlert}>Alert anlegen</button>
        </div>
        {status ? <p className="success-text">{status}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </SectionCard>

      <SectionCard title="Aktive Regeln" subtitle="Uebersicht ueber definierte Preisgrenzen.">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Kraftstoff</th>
                <th>Maximalpreis</th>
                <th>Radius</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.name}</td>
                  <td>{rule.fuel_type.toUpperCase()}</td>
                  <td>{rule.max_price.toFixed(3)} EUR</td>
                  <td>{rule.radius_km} km</td>
                  <td>{rule.enabled ? "Aktiv" : "Pausiert"}</td>
                  <td>
                    <button className="ghost-button" onClick={() => deleteAlert(rule.id)}>Loeschen</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Alert-Historie" subtitle="Interne Benachrichtigungs- und Pruefereignisse.">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Zeitpunkt</th>
                <th>Tankstelle</th>
                <th>Preis</th>
                <th>Nachricht</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>{new Date(event.triggered_at).toLocaleString("de-DE")}</td>
                  <td>{event.station_name}</td>
                  <td>{event.price.toFixed(3)} EUR</td>
                  <td>{event.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </>
  );
}
