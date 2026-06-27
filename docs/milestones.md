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

## Milestone 1 — Basic memory records ✅

**Goal:** Store and retrieve generic memory records.

**Delivered:**

- `MemoryRecord` SQLAlchemy model and migration
- `POST /memories`, `GET /memories/{id}`, `GET /memories`
- Namespace, metadata, provenance, timestamps
- Filters by namespace, actor, type, and source
- Unit and integration tests

## Milestone 2 — Working memory ✅

**Goal:** Active short-term memory separate from durable records.

**Delivered:**

- `WorkingMemoryItem` model and migration
- Session/task-scoped retrieval
- TTL with automatic expiry filtering
- Create, replace (upsert), update, get, and list endpoints
- Unit and integration tests for expiry and session isolation

## Milestone 3 — Episodic memory ✅

**Goal:** Store ordered event sequences as episodes.

**Delivered:**

- `Episode` and `EpisodicEvent` models and migration
- `POST /episodes`, append events, list, get, and replay endpoints
- Session/task grouping and event provenance
- Ordered replay API
- Unit and integration tests

## Milestone 4 — Semantic memory ✅

**Goal:** Store durable facts with confidence, evidence, and versioning.

**Delivered:**

- `SemanticMemory` and `SemanticEvidence` models and migration
- Direct create (`POST /semantic-memory`) and promotion flow (`POST /semantic-memory/promote`)
- Evidence links to memory records, episodes, or episodic events
- Confidence score and version/supersession on contradiction
- List, get, and evidence endpoints with active-only filtering
- Unit tests for promotion rules and integration tests

## Milestone 5 — Association layer ✅

**Goal:** Connect related memories into an explorable graph.

**Delivered:**

- `MemoryAssociation` model and migration
- Manual create and metadata/content auto-linking
- Edge types, weights, and explanations
- Related-memory retrieval with depth-limited traversal
- Traversal deduplication and weight-based ordering
- Unit and integration tests

## Milestone 6 — Hybrid retrieval ✅

**Goal:** Improve recall quality with embeddings and hybrid ranking.

**Delivered:**

- pgvector embeddings on memory records (auto-generated on create)
- Configurable hybrid ranking (similarity, recency, salience, association)
- `POST /recall` with explainable factor breakdown
- `POST /recall/reindex` for embedding backfill
- Unit tests for ranking/embeddings and integration recall scenarios

## Milestone 7 — Consolidation

- Background replay and promotion workers

## Milestone 8 — Forgetting and decay

- Decay policies and archival

## Milestone 9 — Benchmarking and hardening

- Benchmark suite and production readiness

See [dendridb_milestone_roadmap.md](../dendridb_milestone_roadmap.md) for detailed user stories and acceptance criteria.
