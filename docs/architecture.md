# Architecture

DendriDB is organized as a modular Python application with clear separation between API, core infrastructure, models, services, and workers.

## High-level components

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI API │────▶│  Services   │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                     ┌──────────────┐     ┌─────▼──────┐
                     │   Workers    │────▶│ PostgreSQL │
                     └──────────────┘     └────────────┘
```

## Package layout

| Package | Purpose |
|---------|---------|
| `dendridb.api` | HTTP routes and application factory |
| `dendridb.config` | Settings and environment configuration |
| `dendridb.core` | Database engine and session management |
| `dendridb.models` | SQLAlchemy models |
| `dendridb.services` | Business logic (CRUD, recall, jobs) |
| `dendridb.memory` | Memory layer helpers (embeddings, decay, consolidation) |
| `dendridb.ranking` | Hybrid retrieval ranking |
| `dendridb.benchmark` | Benchmark scenarios and reporting |
| `dendridb.workers` | Background job helpers |
| `dendridb.cli` | Command-line tools (`consolidate`, `decay`, `benchmark`) |

## Data store

PostgreSQL is the primary data store. The Docker image includes **pgvector** for embedding-based hybrid recall.

## Configuration

Settings are loaded from environment variables and optional `.env` file via Pydantic Settings. See `.env.example` for available options.

## Migrations

Schema changes are managed with Alembic. Migration scripts live in `alembic/versions/`.

## Design principles

- Python-first implementation
- Testable modules with unit, integration, and e2e coverage
- Explainable hybrid recall with factor breakdowns
- Docker-based local development
- CLI and API parity for background jobs (consolidation, decay)
