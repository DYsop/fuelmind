#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="FuelMind"

run_compose() {
  cd "$SCRIPT_DIR"
  if docker info >/dev/null 2>&1; then
    docker compose "$@"
    return
  fi

  if sudo -n docker info >/dev/null 2>&1; then
    sudo -n docker compose "$@"
    return
  fi

  cat >&2 <<'EOF'
Docker Compose ist fuer den aktuellen Benutzer noch nicht passwortlos freigegeben.

Fuehre einmal das Setup fuer FuelMind-Docker-Rechte aus:
  bash scripts/install_fuelmind_sudo.sh

Danach funktionieren fuelmind.sh und die Windows-Starter automatisch.
EOF
  exit 1
}

show_help() {
  cat <<'EOF'
FuelMind NAS helper

Verwendung:
  bash fuelmind.sh                Startet FuelMind
  bash fuelmind.sh start          Startet FuelMind
  bash fuelmind.sh rebuild        Baut neu und startet FuelMind
  bash fuelmind.sh stop           Stoppt FuelMind
  bash fuelmind.sh restart        Startet FuelMind neu
  bash fuelmind.sh status         Zeigt Containerstatus
  bash fuelmind.sh logs           Zeigt Backend-Logs live
  bash fuelmind.sh frontend-logs  Zeigt Frontend-Logs live
  bash fuelmind.sh health         Prueft den Health-Endpunkt
  bash fuelmind.sh help           Zeigt diese Hilfe
EOF
}

command="${1:-start}"

case "$command" in
  start)
    echo "Starte ${PROJECT_NAME} ..."
    run_compose up -d
    run_compose ps
    ;;
  rebuild)
    echo "Baue ${PROJECT_NAME} neu und starte es ..."
    run_compose up -d --build
    run_compose ps
    ;;
  stop)
    echo "Stoppe ${PROJECT_NAME} ..."
    run_compose down
    ;;
  restart)
    echo "Starte ${PROJECT_NAME} neu ..."
    run_compose down
    run_compose up -d
    run_compose ps
    ;;
  status)
    run_compose ps
    ;;
  logs)
    run_compose logs -f backend
    ;;
  frontend-logs)
    run_compose logs -f frontend
    ;;
  health)
    curl http://localhost:8000/api/health
    echo
    ;;
  help|-h|--help)
    show_help
    ;;
  *)
    echo "Unbekannter Befehl: $command" >&2
    echo
    show_help
    exit 1
    ;;
esac
