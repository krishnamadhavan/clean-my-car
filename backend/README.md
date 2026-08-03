# Clean My Car — Backend

FastAPI service for the Clean My Car subscription platform.

## Stack

- **Python 3.12** + **FastAPI** + **Uvicorn**
- **SQLAlchemy 2 (async)** + **asyncpg** + **PostgreSQL 16**
- **Alembic** for migrations
- Runs via **Docker Compose** from the monorepo root

**Database ER diagram:** [`docs/diagrams/database-er.svg`](../docs/diagrams/database-er.svg) (update on every schema change).

## Local commands

Prefer Make targets from the **repository root** (see root `Makefile`).

```bash
# from monorepo root
make up          # start API + Postgres
make logs        # follow logs
make migrate     # run Alembic migrations (app DB)
make test        # ephemeral test DB cleanmycar_test → pytest → drop
make coverage    # same as test + coverage ≥95% (HTML: backend/htmlcov/index.html)
make pre-commit-install  # once: enable pre-commit git hooks (Ruff)
make down        # stop stack
```

**Tests use a separate database** (`cleanmycar_test` by default). Pytest creates it,
runs migrations, then drops it when the suite finishes. The running app keeps using
`cleanmycar` (or your normal `POSTGRES_DB`).

## API docs

With the stack running, **two** Swagger UIs:

| Surface | Swagger UI | OpenAPI JSON | Base path |
|---------|------------|--------------|-----------|
| **Consumer** (iOS / public product) | http://localhost:8000/docs | http://localhost:8000/openapi.json | `/api/v1` |
| **Ops** (master data / field tools) | http://localhost:8000/ops/docs | http://localhost:8000/ops/openapi.json | `/api/v1/ops` |

Also: ReDoc at `/redoc` (consumer) and `/ops/redoc` (ops).

- Health: http://localhost:8000/api/v1/health
- Ops health: http://localhost:8000/api/v1/ops/health
- Ready (DB): http://localhost:8000/api/v1/ready

Ops inventory: [`docs/OPS_API_INVENTORY.md`](../docs/OPS_API_INVENTORY.md).

### Ops auth (Module 1)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/ops/auth/login` | Email/password → ops access + refresh |
| POST | `/api/v1/ops/auth/logout` | Revoke ops refresh token |
| POST | `/api/v1/ops/auth/token/refresh` | Rotate ops tokens |
| GET | `/api/v1/ops/auth/me` | Current operator (`Authorization: Bearer` ops JWT) |

Ops JWTs use `type=ops_access` and **cannot** call consumer `/me` routes (and consumer tokens cannot call ops).

**Bootstrap operator** (optional, local/dev): set env vars, then restart the API.
Creates the user if that email is not already present (safe if other operators exist):

```bash
OPS_BOOTSTRAP_EMAIL=admin@example.com
OPS_BOOTSTRAP_PASSWORD=changeme12
OPS_BOOTSTRAP_NAME=Admin
```

Then: `make restart` (or restart `api`) and `POST /api/v1/ops/auth/login`.


## Package layout

```
backend/
  src/app/
    api/
      deps.py              # shared dependencies (DB, auth)
      v1/
        router.py
        endpoints/         # health, auth, …
    core/                  # settings, security, phone, exceptions
    db/                    # engine, session, base, mixins
    models/                # SQLAlchemy models
    schemas/               # Pydantic request/response models
    services/              # domain services (auth, sms, …)
    main.py
  alembic/                 # migrations
  tests/
  Dockerfile
  pyproject.toml
```

## Auth (Module 1)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/auth/otp/request` | Send OTP |
| POST | `/api/v1/auth/otp/verify` | Verify OTP → access + refresh tokens |
| POST | `/api/v1/auth/token/refresh` | Rotate tokens |
| POST | `/api/v1/auth/logout` | Revoke refresh token |

In non-production environments the request OTP response includes `debug_otp` for local testing.

## Profile (Module 2)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/me` | Current profile + flags |
| PATCH | `/api/v1/me` | Update name / email |
| POST | `/api/v1/me/deactivate` | Soft-deactivate (revokes sessions) |
| DELETE | `/api/v1/me` | Request account deletion (soft-delete) |

Requires `Authorization: Bearer <access_token>`.

**Re-signup after delete (Option B):** same phone cannot complete OTP login until
`ACCOUNT_DELETION_COOLOFF_DAYS` have passed (default **1**). After cool-off, OTP
verify reactivates the account. During cool-off, verify returns `403` with code
`account_deletion_cooling_off` and `details.available_at`.

```bash
make migrate   # apply users / otp / refresh_tokens / deleted_at
```

## Location (Module 3)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/cities` | Active cities only |
| GET | `/api/v1/cities/{city_id}/societies` | Live societies (`q`, `page`, `page_size`) |
| GET | `/api/v1/societies/{society_id}` | Society detail + service weekdays |
| GET | `/api/v1/me/location` | User city/society (auth) |
| PUT | `/api/v1/me/location` | Set city + live society (auth) |

`service_weekdays`: `0=Mon` … `6=Sun` (exactly three for v1). Non-serviceable societies never appear in list/detail for consumers.
