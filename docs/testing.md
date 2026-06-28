# Testing Guide

## Test layout

```text
tests/
├── unit/           Fast, isolated tests
├── integration/    Tests requiring PostgreSQL
├── e2e/            Tests against a running API
└── fixtures/       Shared fixtures
```

## Running tests

```bash
make test-unit
make test-integration
make test-e2e
make test            # unit + integration
```

## Integration tests

Start PostgreSQL first:

```bash
make docker-up
RUN_INTEGRATION_TESTS=1 make test-integration
```

## End-to-end tests

End-to-end tests exercise the full memory lifecycle across all milestones in one HTTP flow.

**Default (ASGI + PostgreSQL)** — no separate API process required:

```bash
make docker-up
make test-e2e
```

This runs the app in-process over HTTP against a real PostgreSQL database, the same way integration tests do, but as one orchestrated journey through every layer.

**Live API (optional black-box mode)** — hits a running server:

```bash
make docker-up-all
make test-e2e-live
```

Optional: set `E2E_BASE_URL` (default `http://localhost:8000`).

The full flow covers health probes, memory records, working memory, episodes, semantic promotion, associations, recall, consolidation, and decay/lifecycle endpoints.

## Pytest markers

| Marker | Usage |
|--------|-------|
| `unit` | No external dependencies |
| `integration` | Requires PostgreSQL |
| `e2e` | Requires running API |

## CI

GitHub Actions mirrors local setup: each job runs `make setup`, then `make lint`, `make test-unit`, or `make migrate` + `make test-integration` (with a PostgreSQL service container). A Docker build check runs on every push and pull request.

## Writing tests

- Prefer unit tests for validators, ranking helpers, and pure logic
- Use integration tests for database and API interactions
- Use e2e tests sparingly for full-stack smoke checks
