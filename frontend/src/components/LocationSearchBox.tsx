import type { LocationSearchItem } from "../api/types";
import { MapPicker } from "./MapPicker";

type LocationSearchBoxProps = {
  label: string;
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  searching: boolean;
  results: LocationSearchItem[];
  onSelect: (item: LocationSearchItem) => void;
  placeholder?: string;
  helperText?: string;
  lat?: number | null;
  lng?: number | null;
  onMapSelect?: (lat: number, lng: number) => void;
  mapHint?: string;
};

export function LocationSearchBox({
  label,
  query,
  onQueryChange,
  onSearch,
  searching,
  results,
  onSelect,
  placeholder = "PLZ, Ort oder Strasse eingeben",
  helperText,
  lat,
  lng,
  onMapSelect,
  mapHint,
}: LocationSearchBoxProps) {
  return (
    <div className="location-search">
      <label>
        {label}
        <div className="location-search-row">
          <input
            value={query}
            placeholder={placeholder}
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                onSearch();
              }
            }}
          />
          <button
            className="secondary-button"
            type="button"
            onClick={onSearch}
            disabled={searching || query.trim().length < 2}
          >
            {searching ? "Suche..." : "Adresse finden"}
          </button>
        </div>
      </label>
      {helperText ? <p className="info-text">{helperText}</p> : null}
      {results.length > 0 ? (
        <div className="location-results">
          {results.map((item) => (
            <button
              key={`${item.label}-${item.lat}-${item.lng}`}
              className="location-result"
              type="button"
              onClick={() => onSelect(item)}
            >
              <strong>{item.post_code || item.city ? [item.post_code, item.city].filter(Boolean).join(" ") : item.label}</strong>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      ) : null}
      {lat != null && lng != null && onMapSelect ? (
        <div className="location-map-block">
          <p className="info-text">
            {mapHint ?? "Alternativ kannst du den Standort direkt in der Karte anklicken."}
          </p>
          <MapPicker lat={lat} lng={lng} onSelect={onMapSelect} />
        </div>
      ) : null}
    </div>
  );
}
