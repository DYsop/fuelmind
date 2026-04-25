import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { PredictionResponse, SettingsResponse, StationListItem } from "../api/types";
import { SectionCard } from "../components/SectionCard";
import { StatCard } from "../components/StatCard";

function buildQuery(params: Record<string, string | number>) {
  return new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)])).toString();
}

export function DashboardPage() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [stations, setStations] = useState<StationListItem[]>([]);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [fuelType, setFuelType] = useState("e10");
  const [radiusKm, setRadiusKm] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    api.settings()
      .then((data) => {
        setSettings(data);
        setFuelType(data.default_fuel_type);
        setRadiusKm(data.default_radius_km);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function refresh() {
    if (settings?.default_lat == null || settings?.default_lng == null) {
      setError("Bitte zuerst in den Einstellungen einen Standardstandort setzen.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const query = buildQuery({
        lat: settings.default_lat,
        lng: settings.default_lng,
        radius_km: radiusKm,
        fuel_type: fuelType,
        limit: 5,
      });
      const cheapest = await api.cheapest(query);
      const recommendation = await api.prediction(query);
      setStations(cheapest.items as StationListItem[]);
      setPrediction(recommendation);
      setLastUpdated(new Date().toLocaleString("de-DE"));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const summary = useMemo(() => {
    if (stations.length === 0) {
      return {
        count: "0",
        bestPrice: "Keine Daten",
      };
    }
    return {
      count: String(stations.length),
      bestPrice: `${stations[0].price?.toFixed(3)} EUR`,
    };
  }, [stations]);

  return (
    <>
      <SectionCard
        title="Live-Dashboard"
        subtitle="Guenstige Tankstellen im Standardgebiet, letzte Aktualisierung und Heuristik."
        action={
          <button className="primary-button" onClick={refresh} disabled={loading}>
            {loading ? "Aktualisiere..." : "Aktualisieren"}
          </button>
        }
      >
        <div className="filters">
          <label>
            Kraftstoff
            <select value={fuelType} onChange={(event) => setFuelType(event.target.value)}>
              <option value="e5">E5</option>
              <option value="e10">E10</option>
              <option value="diesel">Diesel</option>
            </select>
          </label>
          <label>
            Radius (km)
            <input
              type="number"
              min={1}
              max={25}
              value={radiusKm}
              onChange={(event) => setRadiusKm(Number(event.target.value))}
            />
          </label>
          <div className="status-chip">
            {lastUpdated ? `Letzte Aktualisierung: ${lastUpdated}` : "Noch keine Live-Daten geladen"}
          </div>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="stats-grid">
          <StatCard label="Treffer" value={summary.count} hint="Cheapest-Endpoint im Suchradius" />
          <StatCard label="Bester Preis" value={summary.bestPrice} hint="Aktuell guenstigste Tankstelle" />
          <StatCard
            label="Scheduler"
            value={settings?.scheduler_enabled ? "Aktiv" : "Deaktiviert"}
            hint="Backend-Hintergrundjobs"
          />
        </div>
      </SectionCard>

      <SectionCard title="Empfehlung" subtitle="Heuristische Entscheidung fuer den aktuellen Tankzeitpunkt.">
        {prediction ? (
          <div className={`recommendation recommendation-${prediction.recommendation}`}>
            <strong>{prediction.recommendation === "tank_now" ? "Jetzt tanken" : prediction.recommendation === "wait" ? "Eher warten" : "Neutral"}</strong>
            <p>{prediction.reason}</p>
            <small>Konfidenz: {(prediction.confidence * 100).toFixed(0)}%</small>
          </div>
        ) : (
          <p>Nach dem ersten Refresh erscheint hier die aktuelle Empfehlung.</p>
        )}
      </SectionCard>

      <SectionCard title="Top-Tankstellen" subtitle="Preis, Distanz und Oeffnungsstatus auf einen Blick.">
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Preis</th>
                <th>Distanz</th>
                <th>Status</th>
                <th>Adresse</th>
              </tr>
            </thead>
            <tbody>
              {stations.map((station) => (
                <tr key={station.station_id}>
                  <td>{station.name}</td>
                  <td>{station.price?.toFixed(3) ?? "-"}</td>
                  <td>{station.distance_km?.toFixed(1) ?? "-"} km</td>
                  <td>{station.is_open ? "Offen" : "Unbekannt"}</td>
                  <td>{station.address}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </>
  );
}
