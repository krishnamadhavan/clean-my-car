# Ops UI — Clean My Car

Nuxt 4 app for the **internal ops portal** (catalog admin, waitlist triage, pricing, support).

This package is a **scaffold only**. Screens and API clients will be added next; the backend ops surface already lives at `/api/v1/ops/*` (see [`docs/OPS_API_INVENTORY.md`](../docs/OPS_API_INVENTORY.md)).

| Resource | URL (local) |
|----------|-------------|
| Ops UI | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Ops Swagger | http://localhost:8000/ops/docs |

## Prerequisites

- Node.js **20+** (LTS recommended)
- npm 10+
- Backend stack running (`make up` from monorepo root) when calling APIs

## Setup

```bash
# from monorepo root
make ops-ui-install

# or
cd ops-ui
cp .env.example .env   # optional; defaults match local backend
npm install
```

## Development

```bash
# monorepo root
make ops-ui-dev

# or
cd ops-ui && npm run dev
```

Dev server: http://localhost:3000

Runtime config (public):

| Env | Default | Purpose |
|-----|---------|---------|
| `NUXT_PUBLIC_API_BASE` | `http://localhost:8000` | FastAPI origin |
| `NUXT_PUBLIC_OPS_API_PREFIX` | `/api/v1/ops` | Ops routes prefix |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server (port 3000) |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run generate` | Static generation (optional) |

## Layout

```
ops-ui/
├── app/
│   ├── app.vue
│   ├── assets/css/main.css
│   ├── layouts/default.vue
│   └── pages/index.vue      # placeholder dashboard
├── public/
├── nuxt.config.ts
├── package.json
└── .env.example
```

## Design rules

- **Responsive by default** (mobile-first). Layouts must work from ~320px up without horizontal scroll.
- Prefer fluid grids (`minmax`, `auto-fill`), `flex-wrap`, and `clamp()` over fixed widths.
- Wide tables/code: wrap in `.scroll-x` or stack columns on small viewports.

## Out of scope (for now)

- Operator login / token storage
- API client modules / TanStack Query
- Docker image for the UI (backend remains the compose focus)
- Production deploy pipeline beyond optional CI build
