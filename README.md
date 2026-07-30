# Clean My Car

Monorepo for the **Clean My Car** apartment car-cleaning subscription product.

| Path | Status | Description |
|------|--------|-------------|
| `backend/` | Active | FastAPI + PostgreSQL API |
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
| Swagger | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |
| Ready | http://localhost:8000/api/v1/ready |

```bash
make logs          # follow all logs
make migrate       # Alembic upgrade head
make test          # backend tests
make down          # stop stack
make help          # all targets
```

## Monorepo layout

```
clean-my-car/
├── backend/              # FastAPI service
│   ├── src/app/          # application package
│   ├── alembic/          # DB migrations
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── docs/                 # product requirements, design notes
├── ios/                  # (future) native iOS app
├── docker-compose.yml    # local stack: api + db
├── Makefile              # developer commands
├── .env.example
└── README.md
```

Compose and Make live at the **repo root** so future services (`ios` tooling, workers, etc.) share one developer entrypoint.

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

**Scopes (examples):** `api`, `db`, `auth`, `docker`, `ios`, `docs`, `make`

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
