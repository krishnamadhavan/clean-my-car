# Clean My Car

Monorepo for the **Clean My Car** apartment car-cleaning subscription product.

| Path | Status | Description |
|------|--------|-------------|
| `backend/` | Active | FastAPI + PostgreSQL API |
| `ops-ui/` | Scaffold | Nuxt ops portal (internal dashboard) |
| `ios/` | Planned | Native iOS client |
| `docs/` | Active | PRD and product docs |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose v2
- [Make](https://www.gnu.org/software/make/)

## Quick start (backend)

```bash
cp .env.example .env   # or: make env
make up                # API + Postgres
make health            # liveness
make ready             # DB connectivity
```

| Resource | URL |
|----------|-----|
| API | http://localhost:8000 |
| Swagger (consumer) | http://localhost:8000/docs |
| Swagger (ops) | http://localhost:8000/ops/docs |
| Ops UI (Nuxt) | http://localhost:3000 |
| Health | http://localhost:8000/api/v1/health |
| Ready | http://localhost:8000/api/v1/ready |

```bash
make logs          # follow all logs
make migrate       # Alembic upgrade head
make test          # backend tests
make coverage      # tests + coverage (≥95% required; report in backend/htmlcov/)
make format        # ruff fix + format
make lint          # ruff check
make ops-ui-install   # npm install for ops portal
make ops-ui-dev       # Nuxt dev server → http://localhost:3000
make pre-commit-install   # once: run hooks before every git commit
make pre-commit    # ruff + file checks on all files
make down          # stop stack
make help          # all targets
```

### Ops UI (scaffold)

```bash
make up                 # backend + Postgres (if calling APIs later)
make ops-ui-install
make ops-ui-dev         # http://localhost:3000
```

See [`ops-ui/README.md`](ops-ui/README.md). App screens and auth are not built yet; ops APIs are under `/api/v1/ops/*`.

## Monorepo layout

```
clean-my-car/
├── backend/              # FastAPI service
│   ├── src/app/          # application package
│   ├── alembic/          # DB migrations
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── ops-ui/               # Nuxt ops portal (internal)
├── docs/                 # product requirements, design notes
├── ios/                  # (future) native iOS app
├── docker-compose.yml    # local stack: api + db
├── Makefile              # developer commands
├── .env.example
└── README.md
```

Compose and Make live at the **repo root** so backend, ops UI, and future services share one developer entrypoint.

## CI / GitHub Actions

Workflows live under `.github/workflows/`.

| Workflow | When | Stages |
|----------|------|--------|
| **CI** (`ci.yml`) | Push/PR to `main` | Backend: **Lint** → **Test** → **Docker build**; Ops UI: **Build** (path-filtered) |
| **PR Title** (`pr-title.yml`) | Pull requests | Conventional Commits title check |

Backend stages run only when backend-related paths change (`backend/**`, compose, Makefile, CI workflow). Ops UI build runs when `ops-ui/**` changes. The final **`CI`** job is the single gate to mark required in branch protection.

### Branch protection (recommended)

In GitHub → **Settings → Branches → Branch protection rules** for `main`:

1. Require a pull request before merging
2. Require status checks to pass: **`CI`** (and optionally **Conventional Commits title**)
3. Do not allow bypassing the above if you want the same rules for everyone

## Git workflow

### Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable, releasable history |
| `feat/<short-name>` | New features |
| `fix/<short-name>` | Bug fixes |
| `chore/<short-name>` | Tooling, deps, scaffolding |
| `docs/<short-name>` | Documentation only |

Keep branches short-lived. Open PRs into `main`. Prefer small, reviewable commits.

### Conventional Commits

All commits **must** follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(optional-scope): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`

**Scopes (examples):** `api`, `db`, `auth`, `docker`, `ios`, `ops-ui`, `docs`, `make`

**Examples:**

```
feat(api): add health and readiness endpoints
fix(db): correct async session configuration
chore(docker): add compose stack for api and postgres
docs(prd): resolve remaining open product questions
```

Breaking changes: add `!` after type/scope (`feat(api)!: ...`) or a `BREAKING CHANGE:` footer.

```bash
make commit-help   # print reminder
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Product docs

- [Project Requirements Document](docs/PRD.md)
- [API Inventory (consumer)](docs/API_INVENTORY.md)
- [Ops API Inventory](docs/OPS_API_INVENTORY.md)
- [Database ER diagram](docs/diagrams/database-er.svg) — **update on every schema change** ([notes](docs/EER.md))
