.PHONY: setup dev fmt lint test test-unit test-integration test-e2e docker-up docker-down seed benchmark clean migrate

PYTHON ?= python3
VENV ?= .venv
BIN = $(VENV)/bin
PIP = $(BIN)/pip
PYTEST = $(BIN)/pytest
RUFF = $(BIN)/ruff
UVICORN = $(BIN)/uvicorn
ALEMBIC = $(BIN)/alembic

setup: $(VENV)/bin/activate
	$(PIP) install -e ".[dev]"
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

$(VENV)/bin/activate: pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

dev: setup
	$(UVICORN) dendridb.api.main:app --reload --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8000}

fmt:
	$(RUFF) format src tests alembic
	$(RUFF) check --fix src tests alembic

lint:
	$(RUFF) format --check src tests alembic
	$(RUFF) check src tests alembic

test: test-unit test-integration

test-unit:
	$(PYTEST) tests/unit -m "not integration and not e2e" -v

test-integration:
	$(PYTEST) tests/integration -m integration -v

test-e2e:
	$(PYTEST) tests/e2e -m e2e -v

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

migrate: setup
	$(ALEMBIC) upgrade head

seed:
	@echo "Seed data will be added in later milestones."

benchmark:
	@echo "Benchmarks will be added in later milestones."

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
