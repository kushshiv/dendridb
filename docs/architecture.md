# Architecture

DendriDB is organized as a modular Python application with clear separation between API, core infrastructure, models, services, and workers.

## High-level components

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI API │────▶│  Services   │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
         ┌──────────────┐     ┌─────────────────┼──────────────┐
         │ Celery worker│────▶│ PostgreSQL      │              │
         └──────┬───────┘     │ (durable memory)│              │
                │             └─────────────────┘              │
                │             ┌────────────┐     ┌───────────▼──┐
                └────────────▶│   Redis    │     │    Neo4j     │
                              │ (working   │     │ (graph /     │
                              │  memory)   │     │ associations)│
                              └────────────┘     └──────────────┘
```

## Memory layers and stores

| Layer | Store | Notes |
|-------|-------|-------|
| Working memory | **Redis** | Short-term, TTL-native session context |
| Episodic / semantic / records | **PostgreSQL + pgvector** | Durable memory with hybrid recall |
| Associations & graph traversal | **Neo4j** | Relationship graph; synced on every association write |
| Association metadata | **PostgreSQL** | Source of truth for CRUD and listing |
| Background jobs | **Celery + Redis** | Consolidation and decay |

## Package layout

| Package | Purpose |
|---------|---------|
| `dendridb.api` | HTTP routes and application factory |
| `dendridb.config` | Settings and environment configuration |
| `dendridb.core` | Database and Redis clients |
| `dendridb.graph` | Neo4j association sync and graph traversal |
| `dendridb.working_memory` | Redis working memory store |
| `dendridb.models` | SQLAlchemy models |
| `dendridb.services` | Business logic (CRUD, recall, jobs) |
| `dendridb.memory` | Memory layer helpers (embeddings, decay, consolidation) |
| `dendridb.ranking` | Hybrid retrieval ranking |
| `dendridb.benchmark` | Benchmark scenarios and reporting |
| `dendridb.workers` | Celery app and background job executors |
| `dendridb.cli` | Command-line tools |

## Configuration

Settings are loaded from environment variables and optional `.env` file via Pydantic Settings. See `.env.example`.

Required services: **PostgreSQL**, **Redis**, **Neo4j**.

## Migrations

Schema changes are managed with Alembic. Working memory (Redis) and the association graph (Neo4j) do not use Alembic.

## Design principles

- Python-first, brain-inspired layered memory model
- Production stack: Postgres + Redis + Neo4j + Celery
- Testable with the same stack (all services required in CI)
- Explainable hybrid recall with factor breakdowns
