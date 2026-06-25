# Milestones

DendriDB is built incrementally. Each milestone must be runnable, tested, and documented before moving on.

## Milestone 0 — Foundation ✅

**Goal:** Clean Python project skeleton.

**Delivered:**

- FastAPI app with `/health` endpoint
- PostgreSQL via Docker Compose
- Configuration system
- Alembic migrations
- Pytest (unit, integration, e2e)
- Ruff linting and formatting
- Makefile commands
- GitHub Actions CI
- Open-source repo files and docs

## Milestone 1 — Basic memory records

- `MemoryRecord` schema and table
- CRUD/list API endpoints
- Namespace, metadata, timestamps, provenance
- Filters and tests

## Milestone 2 — Working memory

- Session-scoped short-term memory
- TTL/expiry behavior

## Milestone 3 — Episodic memory

- Episodes and episodic events
- Replay utilities

## Milestone 4 — Semantic memory

- Durable facts with confidence and evidence links

## Milestone 5 — Association layer

- Graph edges between memories

## Milestone 6 — Hybrid retrieval

- pgvector embeddings and hybrid ranking

## Milestone 7 — Consolidation

- Background replay and promotion workers

## Milestone 8 — Forgetting and decay

- Decay policies and archival

## Milestone 9 — Benchmarking and hardening

- Benchmark suite and production readiness

See [dendridb_milestone_roadmap.md](../dendridb_milestone_roadmap.md) for detailed user stories and acceptance criteria.
