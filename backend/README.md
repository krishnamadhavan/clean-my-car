# Clean My Car — Backend

FastAPI service for the Clean My Car subscription platform.

## Stack

- **Python 3.12** + **FastAPI** + **Uvicorn**
- **SQLAlchemy 2 (async)** + **asyncpg** + **PostgreSQL 16**
- **Alembic** for migrations
- Runs via **Docker Compose** from the monorepo root

## Local commands

Prefer Make targets from the **repository root** (see root `Makefile`).

```bash
# from monorepo root
make up          # start API + Postgres
make logs        # follow logs
make migrate     # run Alembic migrations
make test        # run backend tests in container
make down        # stop stack
```

## API docs

With the stack running:

- OpenAPI UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Ready (DB): http://localhost:8000/api/v1/ready

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

```bash
make migrate   # apply users / otp / refresh_tokens tables
```
