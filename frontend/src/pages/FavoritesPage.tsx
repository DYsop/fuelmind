import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { FavoriteItem } from "../api/types";
import { SectionCard } from "../components/SectionCard";

export function FavoritesPage() {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function loadFavorites() {
    try {
      setFavorites(await api.favorites());
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    void loadFavorites();
  }, []);

  async function removeFavorite(id: string) {
    try {
      await api.deleteFavorite(id);
      await loadFavorites();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <SectionCard title="Favoriten" subtitle="Gespeicherte Tankstellen mit letztem bekannten Snapshot.">
      {error ? <p className="error-text">{error}</p> : null}
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Label</th>
              <th>Preis</th>
              <th>Letzter Snapshot</th>
              <th>Verlauf</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {favorites.map((favorite) => (
              <tr key={favorite.id}>
                <td>{favorite.name}</td>
                <td>{favorite.label ?? "-"}</td>
                <td>
                  {favorite.latest_price !== null && favorite.latest_price !== undefined
                    ? `${favorite.latest_price.toFixed(3)} EUR`
                    : "-"}
                </td>
                <td>{favorite.latest_snapshot_at ? new Date(favorite.latest_snapshot_at).toLocaleString("de-DE") : "-"}</td>
                <td>{favorite.latest_fuel_type ? `Zuletzt: ${favorite.latest_fuel_type.toUpperCase()}` : "Chart-Platzhalter"}</td>
                <td>
                  <button className="ghost-button" onClick={() => removeFavorite(favorite.id)}>
                    Entfernen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

