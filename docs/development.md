# Development Guide

## Prerequisites

- Python 3.11 or 3.12
- Docker and Docker Compose
- Make

## Initial setup

```bash
make setup
cp .env.example .env
make docker-up    # PostgreSQL only
make migrate
```

## Running the API

```bash
make dev
```

This starts Uvicorn with hot reload on port 8000. Do **not** run `make docker-up-all` at the same time — both bind to port 8000.

To run the full stack in Docker instead (no hot reload):

```bash
make docker-up-all
```

## Code quality

```bash
make lint     # Auto-fix formatting and lint issues
make lint-check  # Verify only (used in CI)
make benchmark   # Smoke benchmark against PostgreSQL
```

## Database migrations

Create a new migration after model changes:

```bash
alembic revision -m "describe change"
alembic upgrade head
```

Or use `make migrate` to apply pending migrations.

## CLI

```bash
dendridb version
```

## Project conventions

- Use `src/dendridb/` package layout
- Add models under `dendridb.models`
- Add routes under `dendridb.api.routes`
- Add business logic under `dendridb.services`
- Keep milestone scope focused

## Environment variables

See `.env.example`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Runtime environment |
| `DEBUG` | `false` | Enable SQL echo and debug mode |
| `API_PORT` | `8000` | HTTP port |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_DB` | `dendridb` | Database name |
