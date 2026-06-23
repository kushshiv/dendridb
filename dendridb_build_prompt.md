# DendriDB Build Prompt

Use this file as the master execution prompt for implementing DendriDB.

Read `dendridb_overview.md` first. Treat that file as the product vision and architecture explanation. Then follow this document to build the actual project.

---

## Master prompt

Build a production-quality open-source project called **DendriDB**, a brain-inspired memory database for AI systems.

This project must be implemented **incrementally in milestones**, not all at once. Each milestone must produce a working, testable, documented state of the system. The implementation should favor clarity, maintainability, and good developer experience over premature complexity.

DendriDB is not a plain vector database or chat history tool. It is a memory architecture inspired by the brain at a systems level: encoding, working memory, episodic memory, semantic memory, association, consolidation, cue-based recall, and forgetting.

## Core implementation philosophy

- Start with Python first.
- Keep architecture modular.
- Every milestone must run locally with Docker.
- Every milestone must have tests.
- Every milestone must have docs.
- Prefer simple working systems over ambitious unfinished systems.
- Only add complexity when the prior milestone is stable.

## Main technology choices

Use these by default unless there is a strong reason to change:

- **Python** as the main implementation language.
- **FastAPI** for the HTTP API.
- **PostgreSQL** as the primary data store.
- **pgvector** for embeddings and semantic similarity.
- **SQLAlchemy** or **SQLModel** for the persistence layer.
- **Alembic** for migrations.
- **Pytest** for tests.
- **Typer** or **Click** for CLI tools.
- **Docker** and **Docker Compose** for local development.
- **GitHub Actions** for CI/CD.
- **Python scripts** for benchmarking and evaluation.

Do not require Rust or TypeScript in the first implementation. The architecture may leave room for future SDKs or optimized components, but the primary project should remain Python-first.

## What the project must eventually support

The full vision includes:

- ingestion and encoding
- working memory
- episodic memory
- semantic memory
- association graph
- hybrid retrieval
- consolidation workers
- forgetting and decay
- benchmarking and explainability

However, these features must be delivered milestone by milestone.

## Repository expectations

Create an open-source ready repository with:

- `README.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `Makefile`
- `docker-compose.yml`
- `.env.example`
- `.github/workflows/`
- `docs/`
- `src/` or `app/`
- `tests/`
- `benchmarks/`
- `scripts/`
- `alembic/`

## Recommended Python project structure

Use a structure similar to:

```text
DendriDB/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── pyproject.toml
├── Makefile
├── docker-compose.yml
├── .env.example
├── .github/
│   └── workflows/
├── docs/
│   ├── overview.md
│   ├── architecture.md
│   ├── milestones.md
│   ├── api.md
│   ├── development.md
│   ├── deployment.md
│   ├── testing.md
│   └── benchmarking.md
├── src/
│   └── dendridb/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── services/
│       ├── workers/
│       ├── ranking/
│       ├── memory/
│       ├── cli/
│       └── config/
├── alembic/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── benchmarks/
│   ├── datasets/
│   ├── scripts/
│   └── reports/
└── scripts/
```

## Milestone-driven build plan

Implement the project in the following milestones.

### Milestone 0: Foundation

Goal: create a clean, runnable Python project skeleton.

Deliver:

- FastAPI app bootstrapped
- PostgreSQL wired with Docker Compose
- health endpoint
- base config system
- Alembic migrations configured
- Pytest configured
- linting and formatting configured
- Makefile commands
- GitHub Actions for lint + tests
- README with local setup

The result must be a clean starting point that any collaborator can clone and run.

### Milestone 1: Basic memory records

Goal: support storing and retrieving generic memory records.

Deliver:

- `MemoryRecord` schema and table
- create/read/list endpoints
- metadata support
- namespace or tenant field
- timestamps and provenance
- simple filters
- unit and integration tests

This is the first working memory database layer.

### Milestone 2: Working memory

Goal: add active short-term memory.

Deliver:

- working memory type and table
- session/task scoped retrieval
- TTL or expiry behavior
- update/replace behavior
- tests for expiration and retrieval

### Milestone 3: Episodic memory

Goal: store sequences of events as episodes.

Deliver:

- `Episode` and `EpisodicEvent` models
- append event endpoint
- session grouping
- replay API or replay utility
- event provenance support
- episode retrieval tests

### Milestone 4: Semantic memory

Goal: store durable facts and stable knowledge.

Deliver:

- semantic memory model
- promotion flow from episodic or direct input
- evidence links back to source memories
- confidence score
- contradiction or version support
- tests for promotion rules

### Milestone 5: Association layer

Goal: connect related memories.

Deliver:

- association edge model
- edge types and weights
- auto-linking by metadata or semantic similarity
- related-memory retrieval
- explainable links
- graph-like traversal helpers

### Milestone 6: Hybrid retrieval

Goal: improve recall quality.

Deliver:

- embeddings support via pgvector
- hybrid ranking formula
- recall endpoint combining similarity, recency, salience, and associations
- explanation output for why a memory matched
- recall evaluation scenarios

### Milestone 7: Consolidation

Goal: add sleep-inspired memory refinement.

Deliver:

- consolidation jobs
- replay recent episodes
- merge duplicates
- promote patterns into semantic memory
- summarization hooks
- worker process and scheduled execution
- tests for consolidation effects

### Milestone 8: Forgetting and decay

Goal: stop memory clutter.

Deliver:

- decay policies
- retrieval strengthening
- pinning
- archival or soft-delete behavior
- decay tests and configuration

### Milestone 9: Benchmarking and hardening

Goal: make the project measurable and ready for broader use.

Deliver:

- benchmark suite
- ingestion latency checks
- recall latency checks
- consolidation runtime checks
- memory growth scenarios
- benchmark reports in markdown and machine-readable format
- stronger docs and contributor workflows

## Implementation rules for every milestone

Every milestone must include:

- updated docs
- migrations if schema changed
- unit tests
- integration tests where relevant
- example usage
- Makefile commands if needed
- CI passing
- Docker-based local run support

Do not leave milestones half-finished.

## Functional design requirements

### Memory model

At the appropriate milestones define and use models such as:

- MemoryRecord
- WorkingMemoryItem
- Episode
- EpisodicEvent
- SemanticMemory
- AssociationEdge
- RetrievalExplanation
- ConsolidationJob
- DecayPolicy

All records should support practical fields like:

- id
- namespace
- actor_id
- memory_type
- content
- metadata
- source
- created_at
- updated_at
- confidence
- salience
- strength
- decay_rate
- provenance
- linked ids or evidence links

### Retrieval

Hybrid retrieval should eventually combine:

- exact filters
- semantic similarity
- recency
- salience
- association strength
- prior successful reuse
- current task or session relevance

The ranking system should be configurable and testable.

### Explainability

Every recall result should eventually be able to say why it was returned, such as:

- recent and high-salience
- semantically similar
- linked to a related episode
- reinforced by previous retrievals
- promoted from repeated events

## Testing expectations

Write tests from the beginning.

### Unit tests

- validators
- ranking helpers
- decay formulas
- promotion rules
- edge-weight logic

### Integration tests

- API and database interaction
- write then recall flows
- episode creation and replay
- semantic promotion
- consolidation job behavior

### End-to-end tests

- local stack boot
- sample ingest
- sample recall
- worker execution
- CLI usage where implemented

## CI/CD expectations

Use GitHub Actions workflows for:

- format checks
- linting
- unit tests
- integration tests using PostgreSQL service container
- Docker build checks
- docs validation
- benchmark smoke tests for later milestones

## Docker and local development

The project must be easy for collaborators to run.

Support this flow:

1. clone repo
2. copy `.env.example` to `.env`
3. run `make setup`
4. run `make docker-up`
5. run `make dev`
6. run `make test`

Provide clear docs for local development.

## Makefile expectations

Include at least:

- `make setup`
- `make dev`
- `make fmt`
- `make lint`
- `make test`
- `make test-unit`
- `make test-integration`
- `make test-e2e`
- `make docker-up`
- `make docker-down`
- `make seed`
- `make benchmark`
- `make clean`

## Benchmarking

Use Python scripts to benchmark:

- ingestion throughput
- retrieval latency
- retrieval quality for fixed scenarios
- consolidation runtime
- storage growth patterns

Keep benchmarks simple at first, then improve them.

## Documentation requirements

Write docs for three audiences:

1. newcomer who wants to understand the idea
2. contributor who wants to build locally
3. operator who wants to run the system

Required docs should include:

- overview
- architecture
- milestones
- API guide
- development guide
- testing guide
- deployment guide
- benchmarking guide

## Open-source release readiness

Prepare the repo for open-source collaboration with:

- chosen license
- contribution guide
- code of conduct
- issue templates
- pull request template
- semantic versioning guidance
- changelog process

## Final instruction

Build DendriDB as a Python-first, milestone-driven project. Optimize later, but make every milestone clean, documented, runnable, and testable.

Do not try to finish the entire vision in one pass. Finish one milestone completely before moving to the next.
