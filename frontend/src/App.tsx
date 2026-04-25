import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { Shell } from "./components/Shell";
import { AlertsPage } from "./pages/AlertsPage";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FavoritesPage } from "./pages/FavoritesPage";
import { SearchPage } from "./pages/SearchPage";
import { SettingsPage } from "./pages/SettingsPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Shell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "/suche", element: <SearchPage /> },
      { path: "/favoriten", element: <FavoritesPage /> },
      { path: "/alarme", element: <AlertsPage /> },
      { path: "/analyse", element: <AnalysisPage /> },
      { path: "/einstellungen", element: <SettingsPage /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}

