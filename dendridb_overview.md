# DendriDB Overview

DendriDB is a brain-inspired memory database for AI systems, built first in Python and designed to grow in milestones. Its purpose is not just to store records like a normal database, but to help an AI system remember experiences, connect related information, strengthen useful memories, forget low-value details, and recall what matters later in a way that resembles how memory works in the brain.

This project should be understood as a memory system, not just a storage system. A normal database is good at exact reads and writes. DendriDB aims to go further by adding memory traces, working memory, episodic memory, semantic memory, associations, replay-based consolidation, and forgetting.

The goal is not to copy biology cell by cell. The goal is to mimic key memory functions at the systems level in a way that is practical, testable, and useful for software.

## Why DendriDB exists

Most AI systems are still weak at memory. They often rely on:

- long prompts
- simple vector retrieval
- recent chat history
- manually inserted summaries
- stateless request-response patterns

That works for many tasks, but it is not enough for long-term learning, continuity, or experience-based recall.

DendriDB is meant to become a memory engine that lets an AI system:

- remember recent context
- store important experiences
- derive stable knowledge from repeated events
- retrieve memories by cue and relevance
- link related memories together
- replay and consolidate memories over time
- forget what is stale or unimportant

## The big idea in simple terms

You can think of DendriDB like this:

1. Something happens.
2. The system encodes it as a memory trace.
3. The trace may live briefly in working memory.
4. Important experiences are stored as episodes.
5. Repeated or important patterns become stable knowledge.
6. Related memories are linked together.
7. Background jobs replay and refine memories.
8. Low-value memories fade unless they are useful again.
9. Future recall uses context, links, and similarity, not just exact matching.

This is what makes DendriDB different from a plain database or a plain vector store.

## Brain-inspired functions we are mimicking

DendriDB is inspired by broad functions of memory in the brain:

- **Encoding**: turning raw input into an internal memory representation.
- **Working memory**: holding active short-term context.
- **Episodic memory**: remembering experiences and event sequences.
- **Semantic memory**: remembering stable facts and concepts.
- **Association**: linking related memories.
- **Consolidation**: replaying and strengthening useful memories.
- **Cue-based recall**: remembering from partial signals.
- **Forgetting**: weakening or archiving stale memories.

These ideas are used as software design inspiration, not as a strict biology simulation.

## What DendriDB is not

DendriDB is not just:

- a vector database
- a chat history store
- a Redis cache with embeddings
- a relational database clone
- a wrapper around an LLM memory prompt

It may use some of those pieces internally, but the project is about combining them into a memory architecture.

## Core memory layers

DendriDB should grow in layers. Each layer should be understandable, testable, and independently useful.

### 1. Input and encoding layer

This layer receives raw events such as:

- messages
- notes
- tool outputs
- agent state changes
- documents
- actions
- errors
- observations

Its job is to normalize them, tag them, enrich them with metadata, and convert them into internal memory traces.

### 2. Working memory layer

This is active short-term context. It should be fast, temporary, and scoped to a session, task, user, or agent.

Examples:

- current task status
- most recent conversation context
- active constraints
- temporary notes
- unresolved issues

This layer should support TTL and easy replacement.

### 3. Episodic memory layer

This stores experiences as events or sessions.

Examples:

- a debugging session
- a planning conversation
- a deployment attempt
- a research run
- a support interaction

Episodic memory matters because not all memory is a fact. Sometimes the system must remember what happened, in what order, and with what outcome.

### 4. Semantic memory layer

This stores more stable knowledge distilled from repeated evidence or trusted inputs.

Examples:

- user preferences
- stable project rules
- known good solutions
- repeated patterns
- learned constraints

This layer should ideally point back to evidence so the system can explain where a fact came from.

### 5. Association layer

This links memories that are related by:

- shared entities
- topic similarity
- time proximity
- same user or task
- causal connection
- support or contradiction
- file or tool overlap

This layer is important because human-like recall is rarely one isolated record. Memory usually spreads through connected ideas.

### 6. Consolidation layer

This is the sleep-inspired layer.

Background jobs should:

- replay recent memories
- merge duplicates
- strengthen useful traces
- derive summaries or patterns
- promote repeated experiences into semantic memory
- update association weights

This helps DendriDB evolve from “a pile of remembered things” into “a refined memory system.”

### 7. Recall layer

This layer answers questions and returns memory bundles.

Recall should use a hybrid approach that can combine:

- exact matches
- embeddings and semantic similarity
- recency
- salience
- memory strength
- graph links
- task context

The goal is better recall quality, not just nearest-neighbor search.

### 8. Forgetting layer

Forgetting is necessary so the system stays useful.

This layer should support:

- decay over time
- reinforcement on reuse
- pinning important memories
- archival instead of hard deletion
- compaction and summarization

## How the whole system works

A simple example flow:

1. An AI assistant receives a user request.
2. The request, context, and actions are encoded into memory traces.
3. Active details go into working memory.
4. The session is recorded as an episode.
5. Related past memories are linked and retrievable.
6. A background consolidator later reviews recent episodes.
7. Repeated insights become semantic memories.
8. Old low-value traces decay or archive.
9. The next time a similar task appears, recall returns not just similar text, but relevant connected experience.

## Why milestones matter for this project

DendriDB is too broad to build all at once. The project should be built in milestones, with each milestone producing a working, tested system.

This approach matters because it:

- reduces complexity
- lowers project risk
- makes debugging easier
- helps contributors understand the system
- keeps the codebase runnable at every stage
- allows architecture changes before too much is built

The right strategy is to start with a simple memory core and add layers one by one.

## Why Python first

DendriDB should start in **Python** because the first challenge is not low-level performance. The first challenge is to discover the right architecture, memory model, ranking behavior, consolidation logic, and developer experience.

Python is the best first choice for this stage because it is:

- fast to build in
- easy to test and refactor
- strong for APIs and background workers
- strong for embeddings, experimentation, and benchmarking
- familiar to many open-source contributors

If later benchmarks show that one specific part is too slow, that part can be optimized or rewritten later. The architecture should allow future evolution, but the first implementation should favor simplicity and learning speed.

## Suggested first implementation stack

For the first public versions, DendriDB should use:

- Python as the main language
- FastAPI for the API
- PostgreSQL for structured storage
- pgvector for semantic indexing
- SQLAlchemy or SQLModel for persistence layer
- Alembic for migrations
- Celery, RQ, or lightweight workers for background jobs
- Pytest for testing
- Docker and Docker Compose for local development
- GitHub Actions for CI/CD
- Typer or Click for CLI tools

This stack is enough to build a serious first version without premature complexity.

## Long-term evolution

The project can evolve later by adding:

- TypeScript SDKs
- admin UI
- more advanced graph infrastructure
- optimized ranking engines
- optional Rust components for bottlenecks
- cloud deployment templates
- multi-tenant production features

But these should come only after the Python-first system is running well and benchmarked.

## Design principles

DendriDB should follow these principles:

- Build in milestones.
- Keep every milestone runnable and testable.
- Favor clarity over cleverness.
- Use brain inspiration without over-claiming biology.
- Prioritize memory quality over feature count.
- Make retrieval explainable.
- Keep docs as important as code.
- Let performance optimization come after architectural learning.

## Summary in one paragraph

DendriDB is a Python-first, brain-inspired memory database for AI systems that stores experiences, links related memories, consolidates useful knowledge, forgets stale details, and retrieves memory through context and association rather than only exact matching. It should be built milestone by milestone so each layer is understandable, testable, and useful before the next one is added.
