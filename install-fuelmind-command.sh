#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/bin"
TARGET_FILE="${TARGET_DIR}/fuelmind"
SHELL_RC="${HOME}/.bashrc"
PATH_SNIPPET='export PATH="$HOME/.local/bin:$PATH"'

mkdir -p "${TARGET_DIR}"

cat > "${TARGET_FILE}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "${PROJECT_DIR}"
exec bash "${PROJECT_DIR}/fuelmind.sh" "\$@"
EOF

chmod +x "${TARGET_FILE}"

if [ -f "${SHELL_RC}" ]; then
  if ! grep -Fq "${PATH_SNIPPET}" "${SHELL_RC}"; then
    printf '\n%s\n' "${PATH_SNIPPET}" >> "${SHELL_RC}"
  fi
else
  printf '%s\n' "${PATH_SNIPPET}" > "${SHELL_RC}"
fi

cat <<EOF
FuelMind-Befehl wurde installiert:
  ${TARGET_FILE}

Ab jetzt kannst du auf dem NAS in neuen SSH-Sitzungen einfach nutzen:
  fuelmind
  fuelmind status
  fuelmind logs
  fuelmind stop
  fuelmind rebuild

Falls die aktuelle Sitzung den Befehl noch nicht kennt, einmal ausfuehren:
  export PATH="\$HOME/.local/bin:\$PATH"
EOF

