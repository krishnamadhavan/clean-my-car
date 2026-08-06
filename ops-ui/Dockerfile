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
RUN npm ci

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------
FROM base AS development

ENV NODE_ENV=development

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN chmod +x /app/docker-entrypoint.dev.sh

EXPOSE 3000

# Host/port also set in package.json "dev" script for local-outside-Docker use
ENTRYPOINT ["/app/docker-entrypoint.dev.sh"]
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
