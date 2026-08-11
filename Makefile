# Clean My Car — monorepo developer commands
# Requires: Docker, Docker Compose v2, Make

.DEFAULT_GOAL := help

COMPOSE        := docker compose
# Full stack includes the ops-ui Compose profile (see docker-compose.yml).
COMPOSE_FULL   := COMPOSE_PROFILES=ops-ui $(COMPOSE)
API_SERVICE    := api
DB_SERVICE     := db
OPS_UI_SERVICE := ops-ui
BACKEND_DIR    := backend
OPS_UI_DIR     := ops-ui

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
build: env ## Build images (including ops-ui profile)
	$(COMPOSE_FULL) build

.PHONY: up
up: env ## Build and start API + Postgres + Ops UI (detached)
	$(COMPOSE_FULL) up --build -d
	@echo ""
	@echo "API:     http://localhost:$${API_PORT:-8000}"
	@echo "Docs:    http://localhost:$${API_PORT:-8000}/docs"
	@echo "Ops UI:  http://localhost:$${OPS_UI_PORT:-3000}"
	@echo "Health:  http://localhost:$${API_PORT:-8000}/api/v1/health"

.PHONY: up-backend
up-backend: env ## Build and start API + Postgres only (no Ops UI)
	$(COMPOSE) up --build -d $(DB_SERVICE) $(API_SERVICE)
	@echo ""
	@echo "API:     http://localhost:$${API_PORT:-8000}"
	@echo "Docs:    http://localhost:$${API_PORT:-8000}/docs"
	@echo "Health:  http://localhost:$${API_PORT:-8000}/api/v1/health"
	@echo "(Ops UI skipped — use make up or make ops-ui-dev)"

.PHONY: up-fg
up-fg: env ## Start full stack in foreground (includes Ops UI)
	$(COMPOSE_FULL) up --build

.PHONY: down
down: ## Stop containers (keep volumes)
	$(COMPOSE_FULL) down

.PHONY: destroy
destroy: ## Stop containers and delete volumes (destructive)
	$(COMPOSE_FULL) down -v

.PHONY: restart
restart: ## Restart all services
	$(COMPOSE_FULL) restart

.PHONY: ps
ps: ## Show container status
	$(COMPOSE_FULL) ps

.PHONY: logs
logs: ## Follow logs (all services)
	$(COMPOSE_FULL) logs -f

.PHONY: logs-api
logs-api: ## Follow API logs
	$(COMPOSE) logs -f $(API_SERVICE)

.PHONY: logs-db
logs-db: ## Follow Postgres logs
	$(COMPOSE) logs -f $(DB_SERVICE)

.PHONY: logs-ops-ui
logs-ops-ui: ## Follow Ops UI logs
	$(COMPOSE_FULL) logs -f $(OPS_UI_SERVICE)

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

# Ephemeral test DB (created/dropped by pytest conftest — not the app DB)
TEST_DB ?= cleanmycar_test
# Shared env + mounts for test / coverage one-off containers
TEST_RUN = $(COMPOSE) run --rm \
	-e APP_ENV=test \
	-e JWT_SECRET_KEY=test-secret-key-not-for-production \
	-e OTP_RESEND_COOLDOWN_SECONDS=0 \
	-e OTP_MAX_REQUESTS_PER_HOUR=100 \
	-e POSTGRES_HOST=db \
	-e POSTGRES_PORT=5432 \
	-e POSTGRES_USER=$${POSTGRES_USER:-cleanmycar} \
	-e POSTGRES_PASSWORD=$${POSTGRES_PASSWORD:-cleanmycar} \
	-e POSTGRES_APP_DB=$${POSTGRES_DB:-cleanmycar} \
	-e POSTGRES_TEST_DB=$(TEST_DB) \
	-e POSTGRES_DB=$(TEST_DB) \
	-e DATABASE_URL=postgresql+asyncpg://$${POSTGRES_USER:-cleanmycar}:$${POSTGRES_PASSWORD:-cleanmycar}@db:5432/$(TEST_DB) \
	-e OPS_BOOTSTRAP_EMAIL= \
	-e OPS_BOOTSTRAP_PASSWORD= \
	-v "$(CURDIR)/$(BACKEND_DIR)/tests:/app/tests" \
	-v "$(CURDIR)/$(BACKEND_DIR)/src:/app/src" \
	-v "$(CURDIR)/$(BACKEND_DIR)/alembic:/app/alembic" \
	-v "$(CURDIR)/$(BACKEND_DIR)/pyproject.toml:/app/pyproject.toml" \
	-v "$(CURDIR)/$(BACKEND_DIR)/uv.lock:/app/uv.lock"

.PHONY: test
test: ## Run backend tests against ephemeral DB cleanmycar_test (create→migrate→pytest→drop)
	$(TEST_RUN) \
		$(API_SERVICE) \
		sh -c "uv sync --frozen --group dev && pytest -q"

.PHONY: coverage
coverage: ## Run tests with coverage on ephemeral test DB (HTML: backend/htmlcov)
	@mkdir -p "$(BACKEND_DIR)/htmlcov"
	$(TEST_RUN) \
		-v "$(CURDIR)/$(BACKEND_DIR)/htmlcov:/app/htmlcov" \
		$(API_SERVICE) \
		sh -c "uv sync --frozen --group dev && \
			pytest -q \
				--cov=app \
				--cov-report=term-missing \
				--cov-report=html:htmlcov \
				--cov-report=xml:htmlcov/coverage.xml && \
			echo '' && echo 'HTML report: $(BACKEND_DIR)/htmlcov/index.html'"

.PHONY: lint
lint: ## Run Ruff linter on backend (container)
	$(COMPOSE) run --rm $(API_SERVICE) \
		sh -c "uv sync --frozen --group dev && ruff check src tests"

.PHONY: format
format: ## Format backend with Ruff (import sort + style)
	$(COMPOSE) run --rm $(API_SERVICE) \
		sh -c "uv sync --frozen --group dev && ruff check --fix src tests && ruff format src tests"

.PHONY: format-check
format-check: ## Check Ruff format/lint without writing
	$(COMPOSE) run --rm $(API_SERVICE) \
		sh -c "uv sync --frozen --group dev && ruff check src tests && ruff format --check src tests"

# ---------------------------------------------------------------------------
# Pre-commit (runs automatically on git commit after install)
# ---------------------------------------------------------------------------

# Prefer PATH; fall back to uv tool install location
PRE_COMMIT := $(shell command -v pre-commit 2>/dev/null || echo "$(HOME)/.local/bin/pre-commit")

.PHONY: pre-commit-install
pre-commit-install: ## Install git hooks so pre-commit runs before every commit
	@if ! command -v pre-commit >/dev/null 2>&1 && [ ! -x "$(HOME)/.local/bin/pre-commit" ]; then \
		echo "Installing pre-commit via uv tool..."; \
		uv tool install pre-commit; \
	fi
	@if ! command -v pre-commit >/dev/null 2>&1 && [ -x "$(HOME)/.local/bin/pre-commit" ]; then \
		echo "Note: add $(HOME)/.local/bin to PATH (e.g. uv tool update-shell)"; \
	fi
	"$(PRE_COMMIT)" install
	@echo ""
	@echo "pre-commit installed for this repo."
	@echo "Hooks run on every 'git commit'. Manual: make pre-commit"

.PHONY: pre-commit
pre-commit: ## Run all pre-commit hooks against the full tree
	@if [ ! -x "$(PRE_COMMIT)" ] && ! command -v pre-commit >/dev/null 2>&1; then \
		echo "Run: make pre-commit-install"; exit 1; \
	fi
	"$(PRE_COMMIT)" run --all-files

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
# Ops UI (Nuxt portal — Docker by default; host npm optional)
# ---------------------------------------------------------------------------

.PHONY: ops-ui-install
ops-ui-install: ## Install ops-ui npm dependencies on the host (optional; not needed for Docker)
	cd $(OPS_UI_DIR) && npm install

.PHONY: ops-ui-dev
ops-ui-dev: env ## Start Ops UI (pulls in healthy api/db via depends_on)
	$(COMPOSE_FULL) up --build -d $(OPS_UI_SERVICE)
	@echo "Ops UI: http://localhost:$${OPS_UI_PORT:-3000}"

.PHONY: ops-ui-dev-host
ops-ui-dev-host: ## Run Nuxt on the host (requires Node 20+ and make ops-ui-install)
	cd $(OPS_UI_DIR) && npm run dev

.PHONY: ops-ui-build
ops-ui-build: ## Production build of ops-ui (host npm)
	cd $(OPS_UI_DIR) && npm run build

.PHONY: ops-ui-preview
ops-ui-preview: ## Preview production ops-ui build (host npm)
	cd $(OPS_UI_DIR) && npm run preview

.PHONY: ops-ui-shell
ops-ui-shell: ## Open a shell in the Ops UI container
	$(COMPOSE_FULL) exec $(OPS_UI_SERVICE) /bin/sh

# ---------------------------------------------------------------------------
# iOS (SwiftUI consumer app under ios/)
# ---------------------------------------------------------------------------

IOS_DIR := ios
IOS_PROJECT := $(IOS_DIR)/CleanMyCar.xcodeproj
IOS_SCHEME := CleanMyCar
# Override: make ios-build IOS_DEST='platform=iOS Simulator,name=iPhone 17 Pro'
IOS_DEST ?= platform=iOS Simulator,name=iPhone 17

.PHONY: ios-open
ios-open: ## Open CleanMyCar.xcodeproj in Xcode
	open "$(IOS_PROJECT)"

.PHONY: ios-build
ios-build: ## Build iOS app for the Simulator (requires Xcode)
	xcodebuild \
		-project "$(IOS_PROJECT)" \
		-scheme "$(IOS_SCHEME)" \
		-destination '$(IOS_DEST)' \
		-configuration Debug \
		build

.PHONY: ios-simulators
ios-simulators: ## List available iOS Simulators
	xcrun simctl list devices available

# ---------------------------------------------------------------------------
# Git helpers (conventional commits)
# ---------------------------------------------------------------------------

.PHONY: commit-help
commit-help: ## Print conventional commit format reminder
	@echo "Conventional Commits: <type>(optional-scope): <description>"
	@echo ""
	@echo "Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert"
	@echo "Scopes (examples): api, db, auth, docker, ios, docs, ops-ui"
	@echo ""
	@echo "Examples:"
	@echo "  feat(api): add health and readiness endpoints"
	@echo "  fix(db): correct async session cleanup"
	@echo "  chore(docker): pin postgres to 16-alpine"
	@echo "  chore(ops-ui): scaffold Nuxt ops portal"
	@echo "  docs: update monorepo README"
	@echo ""
	@echo "Breaking change: footer 'BREAKING CHANGE: ...' or ! after type/scope"
