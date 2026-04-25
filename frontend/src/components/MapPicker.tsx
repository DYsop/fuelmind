import { useEffect, useRef } from "react";
import L, { type LeafletMouseEvent, type Map as LeafletMap } from "leaflet";

type MapPickerProps = {
  lat: number;
  lng: number;
  onSelect: (lat: number, lng: number) => void;
  zoom?: number;
  height?: number;
};

export function MapPicker({ lat, lng, onSelect, zoom = 13, height = 280 }: MapPickerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<L.CircleMarker | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    const map = L.map(containerRef.current, {
      center: [lat, lng],
      zoom,
      scrollWheelZoom: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    markerRef.current = L.circleMarker([lat, lng], {
      radius: 10,
      color: "#115e59",
      fillColor: "#2a6b62",
      fillOpacity: 0.7,
    }).addTo(map);

    map.on("click", (event: LeafletMouseEvent) => {
      onSelect(event.latlng.lat, event.latlng.lng);
    });

    mapRef.current = map;

    return () => {
      markerRef.current = null;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [lat, lng, onSelect, zoom]);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }
    mapRef.current.setView([lat, lng], mapRef.current.getZoom());
    markerRef.current?.setLatLng([lat, lng]);
  }, [lat, lng]);

  return <div ref={containerRef} className="map-picker" style={{ height }} />;
}
