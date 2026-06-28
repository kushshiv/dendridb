# DendriDB Overview

DendriDB is a brain-inspired memory database for AI systems. It helps AI applications remember experiences, connect related information, strengthen useful memories, forget low-value details, and recall what matters later.

See also the root [dendridb_overview.md](../dendridb_overview.md) for the full product vision.

## Current status

**Milestone 8 (Forgetting and decay)** is complete. The project provides:

- FastAPI HTTP API with health, memory, working memory, episodic, semantic, association, recall, consolidation, and decay endpoints
- PostgreSQL via Docker Compose (with pgvector image for future milestones)
- Durable records with pgvector embeddings, session-scoped working memory, episodic events, semantic facts, and memory associations
- Configuration via environment variables
- Alembic migrations
- Pytest test suite
- Ruff linting and formatting
- GitHub Actions CI
- Local development via Makefile

## Memory layers (roadmap)

Future milestones will add:

1. ~~Basic memory records~~ ✅
2. ~~Working memory~~ ✅
3. ~~Episodic memory~~ ✅
4. ~~Semantic memory~~ ✅
5. ~~Association graph~~ ✅
6. ~~Hybrid retrieval~~ ✅
7. ~~Consolidation workers~~ ✅
8. ~~Forgetting and decay~~ ✅
9. Benchmarking and hardening

## Who this is for

- **Newcomers** — start with this overview and the [milestones](milestones.md) doc
- **Contributors** — see [development.md](development.md)
- **Operators** — see [deployment.md](deployment.md)
