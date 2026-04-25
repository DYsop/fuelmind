#!/bin/sh
set -eu

export API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api}"
envsubst '${API_BASE_URL}' < /usr/share/nginx/html/config.template.js > /usr/share/nginx/html/config.js

exec "$@"

