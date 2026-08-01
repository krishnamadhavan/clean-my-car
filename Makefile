# Clean My Car — monorepo developer commands
# Requires: Docker, Docker Compose v2, Make

.DEFAULT_GOAL := help

COMPOSE        := docker compose
API_SERVICE    := api
DB_SERVICE     := db
BACKEND_DIR    := backend

# Colors (optional nicety for help)
CYAN  := \033[36m
RESET := \033[0m

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-18s$(RESET) %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

.PHONY: env
env: ## Create .env from .env.example if missing
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
	else \
		echo ".env already exists"; \
	fi

# ---------------------------------------------------------------------------
# Docker stack
# ---------------------------------------------------------------------------

.PHONY: build
build: env ## Build images
	$(COMPOSE) build

.PHONY: up
up: env ## Build and start API + Postgres (detached)
	$(COMPOSE) up --build -d
	@echo ""
	@echo "API:   http://localhost:$${API_PORT:-8000}"
	@echo "Docs:  http://localhost:$${API_PORT:-8000}/docs"
	@echo "Health: http://localhost:$${API_PORT:-8000}/api/v1/health"

.PHONY: up-fg
up-fg: env ## Start stack in foreground
	$(COMPOSE) up --build

.PHONY: down
down: ## Stop containers (keep volumes)
	$(COMPOSE) down

.PHONY: destroy
destroy: ## Stop containers and delete volumes (destructive)
	$(COMPOSE) down -v

.PHONY: restart
restart: ## Restart all services
	$(COMPOSE) restart

.PHONY: ps
ps: ## Show container status
	$(COMPOSE) ps

.PHONY: logs
logs: ## Follow logs (all services)
	$(COMPOSE) logs -f

.PHONY: logs-api
logs-api: ## Follow API logs
	$(COMPOSE) logs -f $(API_SERVICE)

.PHONY: logs-db
logs-db: ## Follow Postgres logs
	$(COMPOSE) logs -f $(DB_SERVICE)

# ---------------------------------------------------------------------------
# Backend (API container)
# ---------------------------------------------------------------------------

.PHONY: shell
shell: ## Open a shell in the API container
	$(COMPOSE) exec $(API_SERVICE) /bin/bash

.PHONY: api-sh
api-sh: shell ## Alias for shell

.PHONY: migrate
migrate: ## Run Alembic migrations to head
	$(COMPOSE) exec $(API_SERVICE) alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Roll back one Alembic migration
	$(COMPOSE) exec $(API_SERVICE) alembic downgrade -1

.PHONY: migration
migration: ## Create a new Alembic revision (usage: make migration m="add users")
	@if [ -z "$(m)" ]; then \
		echo 'Usage: make migration m="short description"'; \
		exit 1; \
	fi
	$(COMPOSE) exec $(API_SERVICE) alembic revision --autogenerate -m "$(m)"

.PHONY: test
test: ## Run backend tests in a one-off container
	$(COMPOSE) run --rm \
		-e APP_ENV=test \
		-e JWT_SECRET_KEY=test-secret-key-not-for-production \
		-e OTP_RESEND_COOLDOWN_SECONDS=0 \
		-e OTP_MAX_REQUESTS_PER_HOUR=100 \
		-v "$(CURDIR)/$(BACKEND_DIR)/tests:/app/tests" \
		-v "$(CURDIR)/$(BACKEND_DIR)/src:/app/src" \
		-v "$(CURDIR)/$(BACKEND_DIR)/alembic:/app/alembic" \
		-v "$(CURDIR)/$(BACKEND_DIR)/pyproject.toml:/app/pyproject.toml" \
		-v "$(CURDIR)/$(BACKEND_DIR)/uv.lock:/app/uv.lock" \
		$(API_SERVICE) \
		sh -c "uv sync --frozen --group dev && alembic upgrade head && pytest -q"

.PHONY: lint
lint: ## Run Ruff linter in a one-off container
	$(COMPOSE) run --rm $(API_SERVICE) \
		sh -c "uv sync --group dev && ruff check src tests"

.PHONY: format
format: ## Format backend code with Ruff
	$(COMPOSE) run --rm $(API_SERVICE) \
		sh -c "uv sync --group dev && ruff format src tests && ruff check --fix src tests"

.PHONY: ready
ready: ## Hit readiness endpoint (DB check)
	@curl -sf "http://localhost:$${API_PORT:-8000}/api/v1/ready" | python3 -m json.tool

.PHONY: health
health: ## Hit liveness endpoint
	@curl -sf "http://localhost:$${API_PORT:-8000}/api/v1/health" | python3 -m json.tool

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

.PHONY: psql
psql: ## Open psql in the Postgres container
	$(COMPOSE) exec $(DB_SERVICE) \
		psql -U $${POSTGRES_USER:-cleanmycar} -d $${POSTGRES_DB:-cleanmycar}

.PHONY: db-reset
db-reset: ## Drop DB volume and recreate stack (destructive)
	$(COMPOSE) down -v
	$(COMPOSE) up --build -d
	@echo "Waiting for API..."
	@sleep 5
	@$(MAKE) migrate || true

# ---------------------------------------------------------------------------
# Git helpers (conventional commits)
# ---------------------------------------------------------------------------

.PHONY: commit-help
commit-help: ## Print conventional commit format reminder
	@echo "Conventional Commits: <type>(optional-scope): <description>"
	@echo ""
	@echo "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
	@echo "Scopes (examples): api, db, auth, docker, ios, docs"
	@echo ""
	@echo "Examples:"
	@echo "  feat(api): add health and readiness endpoints"
	@echo "  fix(db): correct async session cleanup"
	@echo "  chore(docker): pin postgres to 16-alpine"
	@echo "  docs: update monorepo README"
	@echo ""
	@echo "Breaking change: footer 'BREAKING CHANGE: ...' or ! after type/scope"
