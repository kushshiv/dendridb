# Hardening Guide

This guide covers operational readiness, quality guardrails, and contributor practices for keeping DendriDB stable as it evolves.

## Health endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Overall status with database check |
| `GET /health/live` | Process liveness (always 200 when running) |
| `GET /health/ready` | Readiness (503 when PostgreSQL is unavailable) |

Use `/health/live` for liveness probes and `/health/ready` for readiness probes in orchestrators such as Kubernetes.

## Database reliability

- Connection pooling uses `pool_pre_ping=True` to drop stale connections.
- Run `make migrate` before starting the API or workers in each environment.
- Integration tests apply Alembic migrations to stay aligned with production schema.

## Benchmark guardrails

Run smoke benchmarks locally before merging retrieval or consolidation changes:

```bash
make docker-up
make migrate
make benchmark
```

The smoke suite checks:

- Memory ingestion completes for the fixture dataset
- Recall returns expected keywords for fixed queries
- Consolidation completes and promotes repeated episode patterns

Full benchmarks (`make benchmark-full`) add more records and write timestamped reports under `benchmarks/reports/`.

## CI expectations

GitHub Actions runs:

- `make lint-check` — formatting and lint rules
- `make test-unit` — fast isolated tests
- `make migrate` + `make test-integration` — database and API integration tests
- `make migrate` + `make test-e2e` — full-memory-flow end-to-end test

Keep benchmark datasets deterministic. Avoid timing-based assertions in CI; prefer quality hit-rate and job completion checks.

## Production checklist

- Set `ENVIRONMENT=production` and disable `DEBUG`
- Configure PostgreSQL credentials via environment variables (never commit `.env`)
- Run migrations as a separate deploy step
- Monitor `/health/ready` for database connectivity
- Schedule consolidation and decay jobs per namespace as needed
- Back up PostgreSQL regularly; DendriDB stores durable state in PostgreSQL

## Contributor workflow

1. Run `make lint` to auto-fix formatting before committing.
2. Run `make test` with `RUN_INTEGRATION_TESTS=1` when changing database or API behavior.
3. Update docs when adding endpoints, settings, or benchmark datasets.
4. Add or adjust benchmark fixtures when changing recall ranking or consolidation behavior.

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [development.md](development.md) for setup details.
