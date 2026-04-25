#!/usr/bin/env bash
set -euo pipefail

CURRENT_USER="$(id -un)"
DOCKER_BIN="$(command -v docker || true)"
SUDOERS_FILE="/etc/sudoers.d/fuelmind-docker"

if [[ -z "${DOCKER_BIN}" ]]; then
  echo "Docker wurde auf diesem NAS nicht gefunden." >&2
  exit 1
fi

ENTRY="${CURRENT_USER} ALL=(root) NOPASSWD: ${DOCKER_BIN}"

echo "Richte passwortlosen sudo-Zugriff fuer Docker ein ..."
echo "Es wird jetzt einmal dein sudo-Passwort benoetigt."

printf '%s\n' "${ENTRY}" | sudo tee "${SUDOERS_FILE}" >/dev/null
sudo chmod 440 "${SUDOERS_FILE}"
sudo visudo -cf "${SUDOERS_FILE}"

echo
echo "Fertig. Ab jetzt darf ${CURRENT_USER} Docker ohne sudo-Passwort ausfuehren."
echo "Test:"
echo "  sudo -n docker compose version"
