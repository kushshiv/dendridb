# DendriDB Overview

DendriDB is a brain-inspired memory database for AI systems. It helps AI applications remember experiences, connect related information, strengthen useful memories, forget low-value details, and recall what matters later.

See also the root [dendridb_overview.md](../dendridb_overview.md) for the full product vision.

## What the project provides

- FastAPI HTTP API with health, memory, working memory, episodic, semantic, association, recall, consolidation, and decay endpoints
- Liveness and readiness health probes for orchestrators
- PostgreSQL with pgvector for embeddings and hybrid recall
- Durable memory records, session-scoped working memory, episodic events, semantic facts, and memory associations
- Consolidation and decay jobs (API + CLI)
- Benchmark suite with smoke and standard datasets
- Configuration via environment variables, Alembic migrations, and Docker Compose
- Pytest suite (unit, integration, e2e), Ruff linting, and GitHub Actions CI

## Memory layers

DendriDB implements these layers end to end:

| Layer | Purpose |
|-------|---------|
| Memory records | Durable generic memories with metadata, salience, and embeddings |
| Working memory | Short-term, session-scoped context with TTL |
| Episodic memory | Ordered event sequences grouped into episodes |
| Semantic memory | Stable facts with evidence, confidence, and versioning |
| Associations | Graph links between memories with weights and explanations |
| Hybrid recall | Embedding + recency + salience + association ranking |
| Consolidation | Replay episodes, merge duplicates, promote patterns |
| Forgetting | Decay, archival, pinning, and retrieval strengthening |

## Who this is for

- **Newcomers** — start with this overview, then [architecture.md](architecture.md) and [api.md](api.md)
- **Contributors** — see [development.md](development.md) and [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Operators** — see [deployment.md](deployment.md) and [hardening.md](hardening.md)
