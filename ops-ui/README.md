# Ops UI — Clean My Car

Nuxt 4 app for the **internal ops portal** (catalog admin, waitlist triage, pricing, support).

| Resource | URL (local) |
|----------|-------------|
| Ops UI | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Ops Swagger | http://localhost:8000/ops/docs |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose v2 (recommended path)
- Optional host Node: **20+** (LTS) if you prefer `make ops-ui-dev-host`
- Backend stack (started with Ops UI via `make up`)

## Docker (default)

Ops UI is a first-class compose service (`ops-ui`), same as `api` and `db`.

```bash
# monorepo root
make up                 # db + api + ops-ui
# open http://localhost:3000

make logs-ops-ui        # follow Nuxt logs
make ops-ui-shell       # shell in the container
make ops-ui-dev         # start/rebuild only the ops-ui service
make down
```

| Compose detail | Value |
|----------------|--------|
| Service name | `ops-ui` |
| Container | `cmc-ops-ui` |
| Image target | `development` (live reload) |
| Host port | `OPS_UI_PORT` (default `3000`) |
| Source mount | `./ops-ui` → `/app` |
| `node_modules` | named volume `ops_ui_node_modules` (Linux modules from the image) |

The SPA calls the API from the **browser**, so `NUXT_PUBLIC_API_BASE` must be a host-reachable URL (default `http://localhost:8000`), not the Docker network hostname `api`.

**Port coupling:** if you change `API_PORT` in the root `.env`, also set `NUXT_PUBLIC_API_BASE` to the same host port (e.g. `API_PORT=8080` → `NUXT_PUBLIC_API_BASE=http://localhost:8080`). Compose cannot derive that URL from `API_PORT` alone.

Production image (CI / deploy):

```bash
docker build -t clean-my-car-ops-ui:local --target production ./ops-ui
```

## Host Node (optional)

```bash
make ops-ui-install
make ops-ui-dev-host    # http://localhost:3000
# or: cd ops-ui && npm run dev
```

Copy env if you need overrides:

```bash
cd ops-ui
cp .env.example .env
```

## Runtime config (public)

| Env | Default | Purpose |
|-----|---------|---------|
| `NUXT_PUBLIC_API_BASE` | `http://localhost:8000` | FastAPI origin (browser); must match published `API_PORT` |
| `NUXT_PUBLIC_OPS_API_PREFIX` | `/api/v1/ops` | Ops routes prefix |
| `OPS_UI_PORT` | `3000` | Host port published by compose |

Root `.env` (from `.env.example`) is the source of truth for compose.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Dev server (`0.0.0.0:3000`) |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run generate` | Static generation (optional) |

## Layout

```
ops-ui/
├── app/
│   ├── app.vue
│   ├── assets/css/main.css
│   ├── components/
│   ├── composables/
│   ├── layouts/
│   ├── middleware/
│   ├── pages/
│   ├── plugins/
│   ├── types/
│   └── utils/
├── public/
├── Dockerfile              # multi-stage: development | production
├── docker-entrypoint.dev.sh
├── .dockerignore
├── nuxt.config.ts
├── package.json
└── .env.example
```

## UI stack

- **Ant Design Vue 4** for all interactive components (layout, forms, tables, feedback).
- **SPA mode** (`ssr: false`) so Ant Design CSS-in-JS styles inject correctly in the browser.
- Brand theme tokens in `app/utils/theme.ts`:
  - Primary: `#4B49AC`, soft `#98BDFF`
  - Secondary: `#7DA0FA`, `#7978E9`, accent `#F3797E`
- Logo: `public/logo.svg` / `logo-mark.svg` (palette-matched); used via `AppLogo` in shell + login; browser icons via head `link` tags

## Design rules

- **Responsive by default** (mobile-first). Use Ant `Grid` / `Row` / `Col` breakpoints and table `scroll.x`.
- Prefer Ant layout patterns over custom CSS.
- Wide tables: wrap with `.ops-table-scroll` when needed.

## Implemented screens (Modules 1–6)

| Route | Module | Purpose |
|-------|--------|---------|
| `/login` | 1 | Operator email/password login |
| `/` | — | Dashboard + waitlist/pricing gap stats |
| `/users`, `/users/:id` | 2 | Search, detail, deactivate/reactivate |
| `/users/:id/vehicle` | 5 | Inspect/correct user vehicle |
| `/cities`, `/cities/:id` | 3 | Cities + societies CRUD |
| `/waitlist`, `/waitlist/:id` | 4 | List/filter/triage |
| `/vehicles`, `/vehicles/:makeId` | 5 | Makes + models + size_tier |
| `/pricing`, `/pricing/:cityId`, `/pricing/quote` | 6 | Tariffs, matrix, quote preview |

Requires backend with bootstrap ops user (see root `.env.example` `OPS_BOOTSTRAP_*`) and CORS origins including the UI origin.

## Out of scope (for now)

- Role-based nav gating
- E2E browser tests
