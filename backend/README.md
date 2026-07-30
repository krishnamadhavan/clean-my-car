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
    api/           # route modules
    core/          # settings, shared utilities
    db/            # engine, session, base
    models/        # SQLAlchemy models
    schemas/       # Pydantic schemas
    main.py        # FastAPI app factory
  alembic/         # migrations
  tests/
  Dockerfile
  pyproject.toml
```
