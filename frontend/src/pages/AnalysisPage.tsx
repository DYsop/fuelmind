import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { api } from "../api/client";
import type { BestTimeResponse, FavoriteItem, LocationSearchItem, StationAnalytics } from "../api/types";
import { LocationSearchBox } from "../components/LocationSearchBox";
import { SectionCard } from "../components/SectionCard";

const ANALYSIS_STATION_KEY = "fuelmind:selected-station";

function buildQuery(params: Record<string, string | number>) {
  return new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)])).toString();
}

type StationOption = {
  stationId: string;
  label: string;
};

export function AnalysisPage() {
  const [selectedStationId, setSelectedStationId] = useState("");
  const [fuelType, setFuelType] = useState("e10");
  const [days, setDays] = useState(7);
  const [lat, setLat] = useState("51.4500");
  const [lng, setLng] = useState("6.7600");
  const [radiusKm, setRadiusKm] = useState("10");
  const [locationQuery, setLocationQuery] = useState("");
  const [locationResults, setLocationResults] = useState<LocationSearchItem[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<LocationSearchItem | null>(null);
  const [locationSearchPending, setLocationSearchPending] = useState(false);
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [rememberedStation, setRememberedStation] = useState<StationOption | null>(null);
  const [analytics, setAnalytics] = useState<StationAnalytics | null>(null);
  const [bestTime, setBestTime] = useState<BestTimeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.settings()
      .then((settings) => {
        setLat(settings.default_lat?.toString() ?? "51.4500");
        setLng(settings.default_lng?.toString() ?? "6.7600");
        setRadiusKm(settings.default_radius_km.toString());
        setFuelType(settings.default_fuel_type);
      })
      .catch(() => undefined);

    api.favorites()
      .then((items) => setFavorites(items))
      .catch(() => undefined);

    const savedStation = localStorage.getItem(ANALYSIS_STATION_KEY);
    if (!savedStation) {
      return;
    }

    try {
      const parsed = JSON.parse(savedStation) as { stationId?: string; stationName?: string };
      if (parsed.stationId) {
        const station = {
          stationId: parsed.stationId,
          label: parsed.stationName ?? `Vorgemerkte Tankstelle (${parsed.stationId})`,
        };
        setRememberedStation(station);
        setSelectedStationId(parsed.stationId);
      }
    } catch {
      localStorage.removeItem(ANALYSIS_STATION_KEY);
    }
  }, []);

  const stationOptions = useMemo(() => {
    const options = favorites.map((item) => ({
      stationId: item.station_id,
      label: item.label ? `${item.label} (${item.name})` : `${item.name} - ${item.address}`,
    }));

    if (rememberedStation && !options.some((item) => item.stationId === rememberedStation.stationId)) {
      return [rememberedStation, ...options];
    }
    return options;
  }, [favorites, rememberedStation]);

  function applyLocation(location: LocationSearchItem) {
    setSelectedLocation(location);
    setLocationQuery(location.label);
    setLocationResults([]);
    setLat(location.lat.toFixed(5));
    setLng(location.lng.toFixed(5));
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
    return null;
  }

  async function loadAnalytics() {
    setError(null);
    try {
      const resolvedLocation = await ensureResolvedLocation();

      if (selectedStationId) {
        setAnalytics(await api.stationAnalytics(selectedStationId, buildQuery({ fuel_type: fuelType, days })));
      } else {
        setAnalytics(null);
      }

      setBestTime(
        await api.bestTime(
          buildQuery({
            lat: resolvedLocation?.lat ?? lat,
            lng: resolvedLocation?.lng ?? lng,
            radius_km: radiusKm,
            fuel_type: fuelType,
          }),
        ),
      );
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <SectionCard title="Analyse" subtitle="Bereichsanalyse per Adresse oder Karte und Detailanalyse per verstaendlicher Tankstellen-Auswahl.">
        <LocationSearchBox
          label="Analysegebiet"
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
            } catch (err) {
              setError((err as Error).message);
            }
          }}
          searching={locationSearchPending}
          results={locationResults}
          onSelect={applyLocation}
          helperText="Fuer die Bereichsanalyse kannst du deinen Ort suchen oder den Mittelpunkt direkt auf der Karte setzen."
          lat={Number(lat)}
          lng={Number(lng)}
          onMapSelect={(nextLat, nextLng) => applyLocation({ label: `Kartenpunkt ${nextLat.toFixed(5)}, ${nextLng.toFixed(5)}`, lat: nextLat, lng: nextLng })}
          mapHint="Ein Klick auf die Karte setzt das Analysegebiet sofort neu."
        />

        <div className="filters search-grid compact-grid">
          <label>
            Tankstelle fuer Detailanalyse
            <select value={selectedStationId} onChange={(event) => setSelectedStationId(event.target.value)}>
              <option value="">Nur Bereichsanalyse</option>
              {stationOptions.map((item) => (
                <option key={item.stationId} value={item.stationId}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Kraftstoff
            <select value={fuelType} onChange={(event) => setFuelType(event.target.value)}>
              <option value="e5">E5</option>
              <option value="e10">E10</option>
              <option value="diesel">Diesel</option>
            </select>
          </label>
          <label>
            Tage
            <input type="number" min={1} max={60} value={days} onChange={(event) => setDays(Number(event.target.value))} />
          </label>
          <label>
            Radius
            <input value={radiusKm} onChange={(event) => setRadiusKm(event.target.value)} />
          </label>
        </div>

        <details className="advanced-panel">
          <summary>Koordinaten manuell bearbeiten</summary>
          <div className="filters search-grid">
            <label>
              Breitengrad
              <input value={lat} onChange={(event) => setLat(event.target.value)} />
            </label>
            <label>
              Laengengrad
              <input value={lng} onChange={(event) => setLng(event.target.value)} />
            </label>
          </div>
        </details>

        <div className="inline-actions">
          <button className="primary-button" onClick={loadAnalytics}>
            Analyse laden
          </button>
        </div>
        {rememberedStation ? <p className="info-text">Vorgemerkte Tankstelle aus der Suche: {rememberedStation.label}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </SectionCard>

      <SectionCard title="Kennzahlen" subtitle="Minimum, Maximum, Durchschnitt und guenstigste Uhrzeit.">
        {analytics ? (
          <div className="stats-grid">
            <div className="card metric-pill">
              <span>Durchschnitt</span>
              <strong>{analytics.average_price.toFixed(3)} EUR</strong>
            </div>
            <div className="card metric-pill">
              <span>Minimum</span>
              <strong>{analytics.minimum_price.toFixed(3)} EUR</strong>
            </div>
            <div className="card metric-pill">
              <span>Maximum</span>
              <strong>{analytics.maximum_price.toFixed(3)} EUR</strong>
            </div>
            <div className="card metric-pill">
              <span>Guenstigste Uhrzeit</span>
              <strong>{analytics.cheapest_hour ?? "-"} Uhr</strong>
            </div>
          </div>
        ) : (
          <p>
            Noch keine stationsbezogene Analyse geladen. Waehle dafuer einfach eine vorgemerkte oder favorisierte Tankstelle
            aus der Liste aus.
          </p>
        )}
      </SectionCard>

      <SectionCard title="Stundenprofil" subtitle="Vorbereitung fuer Tageszeitenanalyse und spaetere Prognosemodelle.">
        {analytics && analytics.hourly_profile.length > 0 ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={analytics.hourly_profile}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="average_price" fill="#0f766e" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="info-text">
            Das Stundenprofil erscheint, sobald fuer eine gespeicherte Tankstelle historische Snapshots vorliegen.
          </p>
        )}
      </SectionCard>

      <SectionCard title="Empfohlene Zeitfenster" subtitle="Einfache Heuristik auf Basis historischer Stundenmittelwerte.">
        {bestTime && bestTime.recommended_windows.length > 0 ? (
          <>
            <p>{bestTime.reason}</p>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={bestTime.recommended_windows}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="average_price" stroke="#be123c" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </>
        ) : (
          <p>
            Noch keine ausreichenden Bereichsdaten vorhanden. Fuehre zuerst eine lokale Synchronisierung ueber
            die Stationssuche aus oder sammle ueber Favoriten und Scheduler weitere Snapshots.
          </p>
        )}
      </SectionCard>
    </>
  );
}
