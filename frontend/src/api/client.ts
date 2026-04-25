import type {
  AlertEvent,
  AlertCheckResponse,
  AlertRule,
  BestTimeResponse,
  CheapestResponse,
  FavoriteItem,
  LocationSearchResponse,
  NearbyResponse,
  PredictionResponse,
  SettingsResponse,
  SyncNearbyResponse,
  StationAnalytics,
} from "./types";

const API_BASE_URL = window.__FUELMIND_CONFIG__?.API_BASE_URL ?? "http://localhost:8000/api";

function formatApiErrorDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object") {
          const maybeMessage = (item as { msg?: unknown }).msg;
          if (typeof maybeMessage === "string") {
            return maybeMessage;
          }
        }
        return JSON.stringify(item);
      })
      .join(" | ");
  }

  if (detail && typeof detail === "object") {
    const maybeMessage = (detail as { msg?: unknown }).msg;
    if (typeof maybeMessage === "string") {
      return maybeMessage;
    }
    return JSON.stringify(detail);
  }

  return "Fehler bei der API-Anfrage";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({ detail: "Unbekannter Fehler" }))) as {
      detail?: unknown;
    };
    throw new Error(formatApiErrorDetail(body.detail));
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request("/health"),
  searchLocations: (query: string, limit = 5) =>
    request<LocationSearchResponse>(`/locations/search?q=${encodeURIComponent(query)}&limit=${limit}`),
  nearbyStations: (query: string) => request<NearbyResponse>(`/stations/nearby?${query}`),
  syncNearby: (payload: unknown) =>
    request<SyncNearbyResponse>("/stations/sync-nearby", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  stationDetail: (stationId: string) => request(`/stations/${stationId}`),
  cheapest: (query: string) => request<CheapestResponse>(`/prices/cheapest?${query}`),
  favorites: () => request<FavoriteItem[]>("/favorites"),
  createFavorite: (payload: unknown) =>
    request("/favorites", { method: "POST", body: JSON.stringify(payload) }),
  deleteFavorite: (favoriteId: string) => request(`/favorites/${favoriteId}`, { method: "DELETE" }),
  alerts: () => request<{ rules: AlertRule[]; events: AlertEvent[] }>("/alerts"),
  createAlert: (payload: unknown) =>
    request<AlertRule>("/alerts", { method: "POST", body: JSON.stringify(payload) }),
  updateAlert: (id: string, payload: unknown) =>
    request<AlertRule>(`/alerts/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteAlert: (id: string) => request(`/alerts/${id}`, { method: "DELETE" }),
  checkAlerts: () => request<AlertCheckResponse>("/alerts/check-now", { method: "POST" }),
  stationAnalytics: (stationId: string, query: string) =>
    request<StationAnalytics>(`/analytics/station/${stationId}?${query}`),
  bestTime: (query: string) => request<BestTimeResponse>(`/analytics/best-time?${query}`),
  prediction: (query: string) => request<PredictionResponse>(`/prediction/recommendation?${query}`),
  settings: () => request<SettingsResponse>("/settings"),
  updateSettings: (payload: unknown) =>
    request("/settings/defaults", { method: "PUT", body: JSON.stringify(payload) }),
};
