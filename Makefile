.PHONY: setup dev fmt lint lint-check test test-unit test-integration test-e2e test-e2e-live docker-up docker-up-all docker-down seed benchmark benchmark-full consolidate decay clean migrate

PYTHON ?= python3
VENV ?= .venv

# Use the local virtualenv when present; otherwise use the active Python (e.g. CI).
ifeq ($(wildcard $(VENV)/bin/python),)
  PY := $(PYTHON)
else
  PY := $(VENV)/bin/python
endif

PIP = $(PY) -m pip
PYTEST = $(PY) -m pytest
RUFF = $(PY) -m ruff
UVICORN = $(PY) -m uvicorn
ALEMBIC = $(PY) -m alembic

setup: $(VENV)/bin/activate
	$(VENV)/bin/pip install -e ".[dev]"
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

$(VENV)/bin/activate: pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

dev: setup
	@$(PY) -c "import asyncio; from dendridb.core.database import check_database_connection; raise SystemExit(0 if asyncio.run(check_database_connection()) else 1)" \
		|| echo "WARNING: PostgreSQL is not reachable on $$(grep POSTGRES_PORT .env 2>/dev/null | cut -d= -f2 || echo 5432). Run 'make docker-up' then 'make migrate' before using /memories."
	$(UVICORN) dendridb.api.main:app --reload --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8000}

fmt: lint

lint:
	$(RUFF) format src tests alembic
	$(RUFF) check --fix src tests alembic

lint-check:
	$(RUFF) format --check src tests alembic
	$(RUFF) check src tests alembic

test: test-unit test-integration test-e2e

test-unit:
	$(PYTEST) tests/unit -m "not integration and not e2e" -v

test-integration: setup migrate
	RUN_INTEGRATION_TESTS=1 $(PYTEST) tests/integration -m integration -v

test-e2e: setup migrate
	RUN_E2E_TESTS=1 $(PYTEST) tests/e2e -m e2e -v

test-e2e-live: setup
	@echo "Requires the API running, e.g. make docker-up-all"
	E2E_LIVE=1 RUN_E2E_TESTS=1 $(PYTEST) tests/e2e -m e2e -v

docker-up:
	docker compose up -d postgres

docker-up-all:
	docker compose up -d --build

docker-down:
	docker compose down

migrate: setup
	$(ALEMBIC) upgrade head

consolidate: setup migrate
	$(PY) -m dendridb.cli.main consolidate run --namespace $${NAMESPACE:-demo}

decay: setup migrate
	$(PY) -m dendridb.cli.main decay run --namespace $${NAMESPACE:-demo}

seed:
	@echo "Seed data command not yet implemented."

benchmark: setup migrate
	$(PY) -m dendridb.cli.main benchmark run --smoke

benchmark-full: setup migrate
	$(PY) -m dendridb.cli.main benchmark run

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
