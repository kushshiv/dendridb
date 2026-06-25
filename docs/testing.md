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

With the full stack running:

```bash
make docker-up
RUN_E2E_TESTS=1 make test-e2e
```

Optional: set `E2E_BASE_URL` (default `http://localhost:8000`).

## Pytest markers

| Marker | Usage |
|--------|-------|
| `unit` | No external dependencies |
| `integration` | Requires PostgreSQL |
| `e2e` | Requires running API |

## CI

GitHub Actions runs lint, unit tests, integration tests with a PostgreSQL service container, and Docker build checks on every push and pull request.

## Writing tests

- Prefer unit tests for validators, ranking helpers, and pure logic
- Use integration tests for database and API interactions
- Use e2e tests sparingly for full-stack smoke checks
