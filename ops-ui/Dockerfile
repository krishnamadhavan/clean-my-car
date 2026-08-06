# syntax=docker/dockerfile:1
# Clean My Car — Ops UI (Nuxt)
#
# Targets:
#   development  — used by docker compose (live reload via bind mounts)
#   production   — slim runtime image (node .output/server)

ARG NODE_VERSION=22

# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------
FROM node:${NODE_VERSION}-alpine AS base

WORKDIR /app

ENV NUXT_HOST=0.0.0.0 \
    NUXT_PORT=3000 \
    HOST=0.0.0.0 \
    PORT=3000

# ---------------------------------------------------------------------------
# Dependencies (layer-cached when package-lock is unchanged)
# ---------------------------------------------------------------------------
FROM base AS deps

COPY package.json package-lock.json ./
# Skip lifecycle scripts: postinstall runs `nuxt prepare`, which needs the full
# source tree (nuxt.config + app/). Scripts run after COPY in later stages.
RUN npm ci --ignore-scripts

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
FROM base AS development

ENV NODE_ENV=development \
    OPS_UI_NODE_MODULES_SEED=/opt/ops-ui/node_modules

# Seed path survives empty named-volume mounts over /app/node_modules.
COPY --from=deps /app/node_modules /opt/ops-ui/node_modules
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Generate .nuxt types after sources exist (deps intentionally skipped prepare).
RUN npx nuxt prepare

# Install entrypoint outside /app so compose bind-mount ./ops-ui:/app cannot
# overwrite the script or its executable bit (Windows/zip checkouts).
COPY docker-entrypoint.dev.sh /usr/local/bin/ops-ui-entrypoint
RUN chmod +x /usr/local/bin/ops-ui-entrypoint

EXPOSE 3000

# Host/port also set in package.json "dev" script for local-outside-Docker use
ENTRYPOINT ["/usr/local/bin/ops-ui-entrypoint"]
CMD ["npm", "run", "dev"]

# ---------------------------------------------------------------------------
# Production build
# ---------------------------------------------------------------------------
FROM base AS build

ENV NODE_ENV=production

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Public runtime config is inlined into the SPA bundle at build time.
# Override via --build-arg when building for non-local environments.
ARG NUXT_PUBLIC_API_BASE=http://localhost:8000
ARG NUXT_PUBLIC_OPS_API_PREFIX=/api/v1/ops
ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE \
    NUXT_PUBLIC_OPS_API_PREFIX=$NUXT_PUBLIC_OPS_API_PREFIX

# nuxt build generates .nuxt as needed (deps skipped prepare)
RUN npm run build

# ---------------------------------------------------------------------------
# Production runner
# ---------------------------------------------------------------------------
FROM base AS production

ENV NODE_ENV=production

COPY --from=build /app/.output ./.output

EXPOSE 3000

USER node

CMD ["node", ".output/server/index.mjs"]
