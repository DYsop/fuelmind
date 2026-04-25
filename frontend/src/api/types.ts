export type FuelType = "e5" | "e10" | "diesel";
export type FuelTypeWithAll = FuelType | "all";
export type Recommendation = "tank_now" | "wait" | "neutral";

export interface StationListItem {
  station_id: string;
  name: string;
  brand?: string | null;
  price?: number | null;
  fuel_type: FuelTypeWithAll;
  distance_km?: number | null;
  is_open?: boolean | null;
  address: string;
  lat: number;
  lng: number;
}

export interface NearbyResponse {
  items: StationListItem[];
  source: string;
  cached: boolean;
  fetched_at: string;
}

export interface SyncNearbyResponse {
  synced_stations: number;
  snapshots_created: number;
  fetched_at: string;
  source: string;
}

export interface FavoriteItem {
  id: string;
  station_id: string;
  label?: string | null;
  name: string;
  brand?: string | null;
  address: string;
  latest_price?: number | null;
  latest_fuel_type?: FuelType | null;
  latest_snapshot_at?: string | null;
}

export interface AlertRule {
  id: string;
  name: string;
  fuel_type: FuelType;
  max_price: number;
  lat: number;
  lng: number;
  radius_km: number;
  enabled: boolean;
  notification_channel: string;
  created_at: string;
  updated_at?: string | null;
}

export interface AlertEvent {
  id: string;
  alert_rule_id: string;
  station_id: string;
  station_name: string;
  fuel_type: FuelType;
  price: number;
  triggered_at: string;
  message: string;
  delivered: boolean;
  delivered_at?: string | null;
}

export interface StationAnalytics {
  station_id: string;
  fuel_type: FuelType;
  average_price: number;
  minimum_price: number;
  maximum_price: number;
  cheapest_hour?: number | null;
  most_expensive_hour?: number | null;
  spread: number;
  observation_count: number;
  hourly_profile: Array<{
    hour: number;
    average_price: number;
    minimum_price: number;
    sample_count: number;
  }>;
}

export interface BestTimeResponse {
  fuel_type: FuelType;
  recommended_windows: Array<{
    hour: number;
    average_price: number;
    sample_count: number;
  }>;
  reason: string;
  confidence: number;
  generated_at: string;
}

export interface PredictionResponse {
  recommendation: Recommendation;
  reason: string;
  confidence: number;
  best_station?: StationListItem | null;
  estimated_saving?: number | null;
}

export interface CheapestResponse {
  items: StationListItem[];
  fuel_type: FuelType;
  fetched_at: string;
}

export interface AlertCheckResponse {
  checked_rules: number;
  events_created: number;
  checked_at: string;
}

export interface SettingsResponse {
  default_lat?: number | null;
  default_lng?: number | null;
  default_radius_km: number;
  default_fuel_type: FuelType;
  scheduler_enabled: boolean;
  notification_mode: string;
  external_api_configured: boolean;
  allow_public_api: boolean;
  frontend_api_base_url: string;
  legal_note: string;
}

export interface LocationSearchItem {
  label: string;
  lat: number;
  lng: number;
  city?: string | null;
  post_code?: string | null;
  street?: string | null;
  house_number?: string | null;
}

export interface LocationSearchResponse {
  items: LocationSearchItem[];
  source: string;
  cached: boolean;
  fetched_at: string;
}
