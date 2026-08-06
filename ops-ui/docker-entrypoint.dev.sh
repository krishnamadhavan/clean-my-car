#!/bin/sh
# Development entrypoint: keep node_modules in sync with package-lock when using
# a named volume over /app/node_modules (bind-mounted source tree).
set -e

SEED_DIR="${OPS_UI_NODE_MODULES_SEED:-/opt/ops-ui/node_modules}"

if [ ! -d node_modules/nuxt ]; then
  if [ -d "$SEED_DIR/nuxt" ]; then
    echo "[ops-ui] Seeding node_modules from image (no network)..."
    mkdir -p node_modules
    # Named volume starts empty; copy preinstalled modules from the image.
    cp -a "$SEED_DIR"/. node_modules/
  else
    echo "[ops-ui] Installing npm dependencies..."
    npm ci
  fi
elif [ package-lock.json -nt node_modules/.package-lock.json ] 2>/dev/null; then
  echo "[ops-ui] package-lock.json is newer than node_modules; reinstalling..."
  npm ci
fi

exec "$@"
