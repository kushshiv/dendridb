# DendriDB

A brain-inspired memory database for AI systems.

DendriDB is not a plain vector store or chat history tool. It is a memory architecture inspired by the brain at a systems level: encoding, working memory, episodic memory, semantic memory, association, consolidation, cue-based recall, and forgetting.

## Quick start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Make

### Local setup

```bash
git clone https://github.com/your-org/dendridb.git
cd dendridb
make setup
cp .env.example .env   # if make setup did not create .env
make docker-up
make migrate
make dev
```

The API will be available at [http://localhost:8000](http://localhost:8000).

### Health check

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "healthy",
  "service": "DendriDB",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "neo4j": "ok"
  }
}
```

### Memory records

```bash
# Create
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","content":"Hello from DendriDB"}'

# List
curl "http://localhost:8000/memories?namespace=demo"
```

See [docs/api.md](docs/api.md) for full API details.

### Troubleshooting

**`POST /memories` fails / `Connection refused` on port 5432**

The API needs PostgreSQL, Redis, and Neo4j running. `make dev` alone only starts the FastAPI server.

1. Start Docker Desktop
2. Run:

```bash
make docker-up
make migrate
```

3. Confirm health shows database ok:

```bash
curl http://localhost:8000/health
```

You should see `"database": "ok"`, `"redis": "ok"`, and `"neo4j": "ok"` in checks. Then retry your request.

**`make dev` fails with `Address already in use` on port 8000**

`make docker-up` starts **PostgreSQL, Redis, and Neo4j** for local development. If the API container is already running on port 8000, stop it:

```bash
docker compose stop api
# or reset the stack:
make docker-down && make docker-up
make dev
```

Alternatively, skip `make dev` and use the Docker API: `make docker-up-all` (API at port 8000, no hot reload).

## Development

| Command | Description |
|---------|-------------|
| `make setup` | Create virtualenv and install dependencies |
| `make dev` | Run API with hot reload |
| `make fmt` | Auto-fix formatting and lint issues (alias for `make lint`) |
| `make lint` | Auto-fix formatting and lint issues |
| `make lint-check` | Verify formatting and lint (CI) |
| `make benchmark` | Run smoke benchmark suite (requires PostgreSQL) |
| `make benchmark-full` | Run full benchmark suite and write reports |
| `make test` | Run unit, integration, and e2e tests (requires PostgreSQL + Redis + Neo4j) |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests (requires PostgreSQL + Redis + Neo4j) |
| `make test-e2e` | Run full-memory-flow e2e test (requires PostgreSQL + Redis + Neo4j) |
| `make test-e2e-live` | Run e2e against a live API (`make docker-up-all`) |
| `make docker-up` | Start PostgreSQL, Redis, and Neo4j (for local `make dev`) |
| `make docker-up-all` | Start full stack: Postgres, Redis, Neo4j, API, and worker |
| `make worker` | Run Celery worker locally (async jobs) |
| `make docker-down` | Stop Docker services |
| `make migrate` | Apply Alembic migrations |
| `make clean` | Remove build artifacts and virtualenv |

Integration and e2e tests require PostgreSQL, Redis, and Neo4j:

```bash
make docker-up
make test
```

## Project structure

```text
src/dendridb/     Application package
alembic/          Database migrations
tests/            Unit, integration, and e2e tests
docs/             Documentation
benchmarks/       Benchmark datasets, scripts, and reports
scripts/          Utility scripts
```

## Documentation

- [Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [Development guide](docs/development.md)
- [Testing guide](docs/testing.md)
- [API guide](docs/api.md)
- [Deployment guide](docs/deployment.md)
- [Hardening guide](docs/hardening.md)
- [Benchmarking guide](docs/benchmarking.md)

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
