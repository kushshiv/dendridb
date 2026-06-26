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
| `dendridb.models` | SQLAlchemy models (`MemoryRecord`, etc.) |
| `dendridb.services` | Business logic (memory record CRUD) |
| `dendridb.memory` | Memory layer abstractions |
| `dendridb.ranking` | Hybrid retrieval ranking |
| `dendridb.workers` | Background consolidation jobs |
| `dendridb.cli` | Command-line tools |

## Data store

PostgreSQL is the primary data store. The Docker image includes **pgvector** for future embedding-based retrieval (Milestone 6).

## Configuration

Settings are loaded from environment variables and optional `.env` file via Pydantic Settings. See `.env.example` for available options.

## Migrations

Schema changes are managed with Alembic. Migration scripts live in `alembic/versions/`.

## Design principles

- Python-first implementation
- Milestone-driven delivery
- Testable modules
- Explainable memory recall (in later milestones)
- Docker-based local development
