# Contributing

## Monorepo notes

- Backend work lives under `backend/`.
- Ops portal (Nuxt) lives under `ops-ui/` — scaffold only; use `make ops-ui-dev`.
- iOS will live under `ios/` (not scaffolded yet).
- Use root `Makefile` and `docker-compose.yml` for local backend development.
- Do not commit secrets. Use `.env` (gitignored); start from `.env.example`.

### Database design / ER diagram (required)

The visual ER diagram (pgAdmin-style export) is:

**[`docs/diagrams/database-er.svg`](docs/diagrams/database-er.svg)**

**Any schema change must update that SVG in the same PR** (with models + Alembic). Short notes live in [`docs/EER.md`](docs/EER.md).

## Commit messages (required)

We use **Conventional Commits** so history stays readable and automation (changelog, versioning) stays possible.

### Format

```
<type>(scope): <description>

<body>

<footer>
```

- **description:** imperative mood, lowercase start preferred, no trailing period
  Good: `add readiness probe`
  Bad: `Added readiness probe.`
- **scope:** optional but preferred when touching a clear area (`api`, `db`, `docker`, `ios`, `ops-ui`, `docs`)

### Types

| Type | When |
|------|------|
| `feat` | User-facing or API capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting; no logic change |
| `refactor` | Internal change; no behavior change |
| `perf` | Performance improvement |
| `test` | Tests only |
| `build` | Build system or dependencies |
| `ci` | CI configuration |
| `chore` | Maintenance that does not fit above |
| `revert` | Revert a previous commit |

### Examples

```
feat(api): expose calendar-month subscription summary
fix(db): handle pro-rated entitlement edge case
chore(docker): pin postgres image to 16-alpine
docs: document make targets for migrations
test(api): cover readiness failure when db is down
```

## Pull requests

1. Branch from latest `main` using the naming scheme in the root README.
2. Keep PRs focused (one concern per PR when practical).
3. Ensure local checks pass for backend changes: `make test` / `make lint` (or rely on CI).
4. Use a conventional commit style for the **PR title** as well (e.g. `chore(backend): ...`). CI validates the title.
5. Wait for the **CI** status check (lint → test → Docker build) before merge when backend paths changed.

### CI stages (backend)

| Stage | Job | What it runs |
|-------|-----|--------------|
| Lint | `Backend · Lint` | `ruff check`, `ruff format --check` |
| Test | `Backend · Test` | `pytest` against Postgres 16 |
| Build | `Backend · Docker build` | Build `backend/Dockerfile` (no registry push) |
| Gate | `CI` | Fails if any required backend stage failed |

Docs-only changes skip backend jobs; the `CI` gate still reports success.

## Backend development

```bash
make env
make up
make migrate
make test
make coverage          # term + HTML; **must be ≥ 95%**
make lint              # ruff check
make format            # ruff fix + format
```

API docs (consumer): http://localhost:8000/docs
API docs (ops): http://localhost:8000/ops/docs

**Coverage gate:** total coverage for `app` must stay **≥ 95%** (`fail_under` in `pyproject.toml`, enforced by `make coverage` and CI).

## Pre-commit (required for local commits)

Install once per clone so hooks run **before every commit**:

```bash
make pre-commit-install
```

Hooks (see `.pre-commit-config.yaml`):

- General: trailing whitespace, EOF, YAML/TOML, large files, private keys
- **Backend Python:** **Ruff** lint (`--fix`) + **Ruff** format

```bash
make pre-commit          # run all hooks on the whole repo
```

Full tests/coverage need Postgres/Docker (`make test` / `make coverage`) before opening a PR.
