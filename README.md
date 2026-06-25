# DendriDB

A brain-inspired memory database for AI systems.

DendriDB is not a plain vector store or chat history tool. It is a memory architecture inspired by the brain at a systems level: encoding, working memory, episodic memory, semantic memory, association, consolidation, cue-based recall, and forgetting.

This repository is built incrementally in milestones. **Milestone 0** provides the project foundation: FastAPI, PostgreSQL, configuration, migrations, tests, and local Docker development.

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
    "database": "ok"
  }
}
```

## Development

| Command | Description |
|---------|-------------|
| `make setup` | Create virtualenv and install dependencies |
| `make dev` | Run API with hot reload |
| `make fmt` | Format code with Ruff |
| `make lint` | Run lint and format checks |
| `make test` | Run unit and integration tests |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests (requires PostgreSQL) |
| `make docker-up` | Start PostgreSQL and API via Docker Compose |
| `make docker-down` | Stop Docker services |
| `make migrate` | Apply Alembic migrations |
| `make clean` | Remove build artifacts and virtualenv |

Integration tests require PostgreSQL:

```bash
make docker-up
RUN_INTEGRATION_TESTS=1 make test-integration
```

## Project structure

```text
src/dendridb/     Application package
alembic/          Database migrations
tests/            Unit, integration, and e2e tests
docs/             Documentation
benchmarks/       Benchmark scripts (later milestones)
scripts/          Utility scripts
```

## Documentation

- [Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [Milestones](docs/milestones.md)
- [Development guide](docs/development.md)
- [Testing guide](docs/testing.md)
- [API guide](docs/api.md)
- [Deployment guide](docs/deployment.md)
- [Benchmarking guide](docs/benchmarking.md)

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
