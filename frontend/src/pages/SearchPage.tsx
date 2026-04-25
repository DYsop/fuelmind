import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { LocationSearchItem, NearbyResponse } from "../api/types";
import { LocationSearchBox } from "../components/LocationSearchBox";
import { SectionCard } from "../components/SectionCard";

const ANALYSIS_STATION_KEY = "fuelmind:selected-station";

function buildQuery(params: Record<string, string | number>) {
  return new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)])).toString();
}

function hasCoordinates(lat: string, lng: string) {
  return lat.trim().length > 0 && lng.trim().length > 0;
}

export function SearchPage() {
  const [form, setForm] = useState({
    lat: "51.4500",
    lng: "6.7600",
    radius_km: "10",
    fuel_type: "e10",
    sort: "price",
  });
  const [locationQuery, setLocationQuery] = useState("");
  const [locationResults, setLocationResults] = useState<LocationSearchItem[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<LocationSearchItem | null>(null);
  const [locationSearchPending, setLocationSearchPending] = useState(false);
  const [data, setData] = useState<NearbyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    api.settings()
      .then((settings) => {
        setForm((current) => ({
          ...current,
          lat: settings.default_lat?.toString() ?? current.lat,
          lng: settings.default_lng?.toString() ?? current.lng,
          radius_km: settings.default_radius_km.toString(),
          fuel_type: settings.default_fuel_type,
        }));
        if (settings.default_lat != null && settings.default_lng != null) {
          setStatus("Dein gespeicherter Standardstandort ist bereits als Fallback hinterlegt.");
        }
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
    setSelectedLocation({
      label: `Kartenpunkt ${lat.toFixed(5)}, ${lng.toFixed(5)}`,
      lat,
      lng,
    });
    setLocationQuery("");
    setLocationResults([]);
    setForm((current) => ({
      ...current,
      lat: lat.toFixed(5),
      lng: lng.toFixed(5),
    }));
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
      throw new Error("Bitte erst einen Ort, eine PLZ oder manuelle Koordinaten eingeben.");
    }
    return null;
  }

  async function onSearch() {
    setError(null);
    setStatus("Suche laeuft...");
    try {
      const resolvedLocation = await ensureResolvedLocation();
      const query = buildQuery({
        lat: resolvedLocation?.lat ?? form.lat,
        lng: resolvedLocation?.lng ?? form.lng,
        radius_km: form.radius_km,
        fuel_type: form.fuel_type,
        sort: form.sort,
      });
      const response = await api.nearbyStations(query);
      setData(response);
      setStatus(
        `${resolvedLocation ? `Standort gesetzt: ${resolvedLocation.label}. ` : ""}Abfrage erfolgreich (${response.items.length} Treffer)`,
      );
    } catch (err) {
      setError((err as Error).message);
      setStatus(null);
    }
  }

  async function saveFavorite(stationId: string) {
    try {
      await api.createFavorite({ station_id: stationId });
      setStatus("Tankstelle wurde als Favorit gespeichert.");
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function syncNearby() {
    setError(null);
    try {
      const resolvedLocation = await ensureResolvedLocation();
      const result = await api.syncNearby({
        lat: resolvedLocation?.lat ?? Number(form.lat),
        lng: resolvedLocation?.lng ?? Number(form.lng),
        radius_km: Number(form.radius_km),
        fuel_type: form.fuel_type,
        sort: form.sort,
      });
      setStatus(
        `${resolvedLocation ? `Standort gesetzt: ${resolvedLocation.label}. ` : ""}${result.synced_stations} Tankstellen synchronisiert, ${result.snapshots_created} Snapshots gespeichert.`,
      );
    } catch (err) {
      setError((err as Error).message);
    }
  }

  function rememberForAnalysis(stationId: string, stationName: string) {
    localStorage.setItem(
      ANALYSIS_STATION_KEY,
      JSON.stringify({
        stationId,
        stationName,
      }),
    );
    setStatus(`"${stationName}" wurde fuer die Analyse vorgemerkt.`);
  }

  return (
    <>
      <SectionCard title="Stationssuche" subtitle="Suche per PLZ, Ort oder Strasse statt ueber nackte Koordinaten.">
        <LocationSearchBox
          label="Ort, PLZ oder Strasse"
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
              setStatus(`Standort vorbereitet: ${items[0].label}`);
            } catch (err) {
              setError((err as Error).message);
            }
          }}
          searching={locationSearchPending}
          results={locationResults}
          onSelect={(item) => {
            applyLocation(item);
            setStatus(`Standort vorbereitet: ${item.label}`);
          }}
          helperText="Gib hier einfach deine PLZ, deinen Ort oder eine Strasse ein. Der beste Treffer wird fuer Suche und Synchronisierung uebernommen."
          lat={Number(form.lat)}
          lng={Number(form.lng)}
          onMapSelect={(lat, lng) => {
            applyCoordinates(lat, lng);
            setStatus(`Standort per Karte gesetzt: ${lat.toFixed(5)}, ${lng.toFixed(5)}`);
          }}
          mapHint="Oder waehle deinen Suchpunkt direkt in der Karte aus."
        />

        {selectedLocation ? <p className="success-text">Aktiver Standort: {selectedLocation.label}</p> : null}

        <div className="filters search-grid compact-grid">
          <label>
            Radius
            <input value={form.radius_km} onChange={(event) => setForm({ ...form, radius_km: event.target.value })} />
          </label>
          <label>
            Kraftstoff
            <select value={form.fuel_type} onChange={(event) => setForm({ ...form, fuel_type: event.target.value })}>
              <option value="e5">E5</option>
              <option value="e10">E10</option>
              <option value="diesel">Diesel</option>
              <option value="all">Alle</option>
            </select>
          </label>
          <label>
            Sortierung
            <select value={form.sort} onChange={(event) => setForm({ ...form, sort: event.target.value })}>
              <option value="price">Preis</option>
              <option value="distance">Distanz</option>
            </select>
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
          <button className="primary-button" onClick={onSearch}>
            Suchen
          </button>
          <button className="secondary-button" onClick={syncNearby}>
            Lokal synchronisieren
          </button>
        </div>
        {status ? <p className="success-text">{status}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </SectionCard>

      <SectionCard title="Ergebnisliste" subtitle="Preis, Distanz, Adresse und Favoritenaktion.">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Analyse</th>
                <th>Preis</th>
                <th>Distanz</th>
                <th>Status</th>
                <th>Adresse</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((station) => (
                <tr key={station.station_id}>
                  <td>{station.name}</td>
                  <td>
                    <button className="ghost-button" onClick={() => rememberForAnalysis(station.station_id, station.name)}>
                      Fuer Analyse merken
                    </button>
                  </td>
                  <td>{station.price?.toFixed(3) ?? "-"}</td>
                  <td>{station.distance_km?.toFixed(1) ?? "-"} km</td>
                  <td>{station.is_open ? "Offen" : "Unbekannt"}</td>
                  <td>{station.address}</td>
                  <td>
                    <button className="ghost-button" onClick={() => saveFavorite(station.station_id)}>
                      Als Favorit speichern
                    </button>
                  </td>
                </tr>
              )) ?? null}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </>
  );
}
