import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/suche", label: "Stationssuche" },
  { to: "/favoriten", label: "Favoriten" },
  { to: "/alarme", label: "Preisalarme" },
  { to: "/analyse", label: "Analyse" },
  { to: "/einstellungen", label: "Einstellungen" },
];

export function Shell() {
  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">FuelMind</p>
          <h1>Lokale Benzinpreis-App fuer dein NAS.</h1>
          <p className="hero-copy">
            Preisabfragen, Historie, Alerts und erste Tankempfehlungen in einer privaten,
            wartbaren Docker-App.
          </p>
        </div>
        <div className="hero-panel">
          <span>Privater Betrieb</span>
          <strong>Tankerkönig + PostgreSQL + Redis</strong>
          <small>Optimiert fuer lokale Netzwerke, NAS-Systeme und Linux-Server.</small>
        </div>
      </header>
      <nav className="main-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="page-grid">
        <Outlet />
      </main>
    </div>
  );
}
