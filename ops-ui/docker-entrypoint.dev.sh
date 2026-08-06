#!/bin/sh
# Development entrypoint: keep node_modules in sync with package-lock when using
# a named volume over /app/node_modules (bind-mounted source tree).
set -e

if [ ! -d node_modules/nuxt ] || [ package-lock.json -nt node_modules/.package-lock.json ] 2>/dev/null; then
  echo "[ops-ui] Installing npm dependencies..."
  npm ci
fi

exec "$@"
