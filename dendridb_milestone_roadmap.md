# DendriDB Milestone Roadmap

This roadmap is written so it can be used directly inside a GitHub Project as milestones, user stories, tasks, bugs, and acceptance criteria.

The idea is simple: each milestone should contain a small set of user stories that describe value from the point of view of a developer, collaborator, AI system, or operator. Each story can be turned into GitHub issues. Bugs, technical tasks, and sub-tasks can then be linked under those stories.

## How to use this roadmap in GitHub

For each milestone:

- Create one GitHub milestone.
- Create user story issues under that milestone.
- Create implementation tasks linked to each story.
- Create bug issues as needed under the same milestone.
- Do not move to the next milestone until the current milestone is runnable, tested, and documented.

Recommended labels:

- `milestone`
- `user-story`
- `task`
- `bug`
- `backend`
- `api`
- `database`
- `docs`
- `testing`
- `devops`
- `benchmark`
- `memory-layer`
- `enhancement`

Recommended issue structure:

- Title
- User story
- Context
- Technical notes
- Acceptance criteria
- Out of scope
- Linked tasks
- Linked bugs

## Milestone 0 — Foundation

### Milestone goal

Create a clean Python-first project foundation that any collaborator can clone, run, test, and understand.

### User stories

#### Story M0-1: Local startup

**As a contributor**, I want to clone the repository and start the project locally with a small number of commands so that I can begin development quickly.

Acceptance criteria:

- Repository contains a clear Python project structure.
- Docker Compose starts PostgreSQL successfully.
- FastAPI app starts locally.
- README explains setup from zero.
- `.env.example` is present and usable.

Suggested linked tasks:

- Initialize repository structure.
- Add `pyproject.toml`.
- Configure FastAPI entrypoint.
- Add Docker Compose for PostgreSQL.
- Add `.env.example`.
- Write README quick start.

Suggested bug examples:

- Docker service does not start on a clean machine.
- Environment variables are missing or inconsistent.
- App boot fails when database is unavailable.

#### Story M0-2: Developer workflow

**As a collaborator**, I want standard commands for setup, linting, testing, and local development so that the project feels predictable and easy to contribute to.

Acceptance criteria:

- Makefile exists with setup, dev, lint, fmt, and test commands.
- Lint and format tooling are configured.
- Pytest runs successfully.
- Pre-commit or equivalent tooling is documented.

Suggested linked tasks:

- Add Makefile.
- Configure Ruff, Black, or chosen lint/format tools.
- Configure Pytest.
- Add contributor instructions.

Suggested bug examples:

- `make test` fails on a clean environment.
- Format and lint rules conflict.

#### Story M0-3: CI baseline

**As a maintainer**, I want CI to validate code quality and test execution so that broken changes are caught early.

Acceptance criteria:

- GitHub Actions run lint checks.
- GitHub Actions run tests.
- CI status is documented in README.
- A health endpoint exists and can be used in smoke checks.

Suggested linked tasks:

- Add GitHub workflow for lint and tests.
- Add `/health` endpoint.
- Add CI badge to README.

Suggested bug examples:

- CI passes locally but fails in GitHub Actions.
- Service boot timing causes flaky smoke checks.

## Milestone 1 — Basic Memory Store

### Milestone goal

Create the first usable memory layer: durable storage and retrieval of generic memory records.

### User stories

#### Story M1-1: Write memory records

**As an application developer**, I want to store a memory record with content and metadata so that the system can retain useful information.

Acceptance criteria:

- API supports creating memory records.
- Records include content, metadata, namespace, timestamps, and source fields.
- Validation errors are handled clearly.
- Stored records persist in PostgreSQL.

Suggested linked tasks:

- Create memory record schema.
- Add database model.
- Add migration.
- Add POST endpoint.
- Add validation tests.

Suggested bug examples:

- Invalid metadata shape causes server crash.
- Missing namespace is not validated correctly.

#### Story M1-2: Read memory records

**As an application developer**, I want to retrieve stored memory records so that my system can use past information.

Acceptance criteria:

- API supports get-by-id.
- API supports list with basic filters.
- Results are returned consistently.
- Integration tests prove write then read flow.

Suggested linked tasks:

- Add GET by ID endpoint.
- Add list endpoint.
- Add filtering by namespace or source.
- Add integration tests.

Suggested bug examples:

- Reading a missing record returns wrong status code.
- Filters return records from the wrong namespace.

#### Story M1-3: Provenance support

**As a developer**, I want each memory to carry provenance details so that future layers can explain where a memory came from.

Acceptance criteria:

- Source metadata is persisted.
- Creator or actor information can be stored.
- Provenance is visible in API responses.

## Milestone 2 — Working Memory

### Milestone goal

Add short-term memory that behaves differently from durable memory.

### User stories

#### Story M2-1: Session-scoped memory

**As an AI system**, I want to store active context for a session or task so that current work stays coherent.

Acceptance criteria:

- Working memory can be stored separately from durable memory.
- Working memory can be fetched by session or task.
- Working memory supports updates.

Suggested linked tasks:

- Create working memory model.
- Add session-scoped endpoints.
- Add update behavior.
- Add tests.

Suggested bug examples:

- Working memory leaks across sessions.
- Updates overwrite the wrong record.

#### Story M2-2: Expiring context

**As a system designer**, I want working memory to expire automatically so that temporary context does not pollute long-term memory.

Acceptance criteria:

- TTL or expiry behavior exists.
- Expired items are filtered or cleaned correctly.
- Expiry behavior is tested.

Suggested bug examples:

- Expired memories still appear in active retrieval.
- Cleanup job removes valid active records.

## Milestone 3 — Episodic Memory

### Milestone goal

Store experiences and event sequences as episodes.

### User stories

#### Story M3-1: Record episodes

**As an AI system**, I want to group related events into an episode so that a full experience can be reconstructed later.

Acceptance criteria:

- Episodes can be created.
- Events can be appended in order.
- Episode metadata can store session, task, and actor context.

Suggested linked tasks:

- Create episode model.
- Create episodic event model.
- Add append endpoint.
- Add ordering tests.

Suggested bug examples:

- Events are returned out of order.
- Episode boundaries are not respected.

#### Story M3-2: Replay an episode

**As a developer**, I want to replay an episode so that later consolidation can learn from it.

Acceptance criteria:

- Replay utility or API exists.
- Episode events are returned in sequence.
- Replay is documented and tested.

## Milestone 4 — Semantic Memory

### Milestone goal

Turn repeated or trusted knowledge into stable semantic memory.

### User stories

#### Story M4-1: Store stable knowledge

**As an AI system**, I want to store stable facts separately from raw episodes so that durable knowledge is easy to retrieve and manage.

Acceptance criteria:

- Semantic memory model exists.
- Semantic records are distinguishable from episodic records.
- Confidence and provenance are stored.

#### Story M4-2: Promote from evidence

**As a system designer**, I want semantic memory to reference supporting evidence so that facts remain explainable.

Acceptance criteria:

- Semantic memory can link to supporting episodes or records.
- Promotion flow exists.
- Promotion rules are tested.

Suggested bug examples:

- Promotion creates duplicate facts repeatedly.
- Evidence links break when source records change.

## Milestone 5 — Association Layer

### Milestone goal

Link memories together into a more brain-like connected memory structure.

### User stories

#### Story M5-1: Create associations

**As the memory engine**, I want to link related memories so that recall can expand beyond isolated records.

Acceptance criteria:

- Association edge model exists.
- Edge type and weight are stored.
- Manual or automatic linking is supported.

#### Story M5-2: Retrieve related memories

**As an AI system**, I want to fetch related memories from a starting memory so that context can expand in a meaningful way.

Acceptance criteria:

- Related-memory retrieval exists.
- Edge weights affect ordering.
- Response includes relationship explanation.

Suggested bug examples:

- Unrelated records are linked too aggressively.
- Traversal returns duplicate related records.

## Milestone 6 — Hybrid Retrieval

### Milestone goal

Make memory recall more useful than simple lookup.

### User stories

#### Story M6-1: Recall by relevance

**As an AI system**, I want recall to combine semantic similarity, recency, salience, and associations so that I get the most useful memories, not just the closest text match.

Acceptance criteria:

- Embeddings are stored and used.
- Recall endpoint supports hybrid ranking.
- Ranking logic is configurable.
- Retrieval tests cover realistic scenarios.

#### Story M6-2: Explain recall

**As a developer**, I want the system to explain why memories were returned so that I can debug and trust the retrieval behavior.

Acceptance criteria:

- Responses include explanation data.
- Explanations mention ranking factors.
- Explanation output is documented.

Suggested bug examples:

- Recall ranking ignores salience.
- Explanations do not match real ranking behavior.

## Milestone 7 — Consolidation

### Milestone goal

Add sleep-inspired replay and memory refinement.

### User stories

#### Story M7-1: Replay recent memory

**As the system**, I want to replay recent episodes so that I can refine what should become stronger long-term memory.

Acceptance criteria:

- Consolidation worker exists.
- Replay can run manually or by job.
- Replay behavior is test-covered.

#### Story M7-2: Promote and merge

**As the system**, I want repeated or overlapping episodes to be merged or promoted so that memory becomes cleaner and more useful over time.

Acceptance criteria:

- Duplicate or near-duplicate handling exists.
- Repeated patterns can become semantic memory.
- Consolidation effects are measurable in tests.

Suggested bug examples:

- Consolidation creates duplicate semantic memories.
- Replay modifies records that should stay immutable.

## Milestone 8 — Forgetting and Decay

### Milestone goal

Keep memory useful by reducing stale noise.

### User stories

#### Story M8-1: Decay low-value memories

**As the memory engine**, I want stale low-value memories to weaken over time so that the system remains focused.

Acceptance criteria:

- Decay policy exists.
- Salience or strength can decrease over time.
- Decay behavior is configurable and tested.

#### Story M8-2: Reinforce useful memories

**As the memory engine**, I want reused memories to strengthen so that useful knowledge stays available.

Acceptance criteria:

- Retrieval strengthening exists.
- Important memories can be pinned.
- Archival or soft-delete flow exists.

Suggested bug examples:

- Pinned memories still decay.
- Reinforcement applies to the wrong records.

## Milestone 9 — Benchmarking and Hardening

### Milestone goal

Make DendriDB measurable, stable, and easier to evolve.

### User stories

#### Story M9-1: Benchmark core flows

**As a maintainer**, I want benchmark scripts for ingestion, recall, and consolidation so that I can measure performance over time.

Acceptance criteria:

- Benchmark scripts exist.
- Sample datasets exist.
- Reports can be generated in machine-readable and markdown format.

#### Story M9-2: Guard quality over time

**As a maintainer**, I want repeatable quality checks so that new changes do not silently reduce recall quality or reliability.

Acceptance criteria:

- Benchmark smoke checks run in CI where practical.
- Core scenarios are documented.
- Hardening docs exist for contributors.

Suggested bug examples:

- Benchmark dataset is inconsistent across runs.
- CI benchmark smoke test is flaky.

## Suggested GitHub issue template for user stories

Use this structure for each story issue:

```md
## User story
As a ...
I want ...
So that ...

## Context
Why this matters and where it fits in the milestone.

## Acceptance criteria
- [ ] ...
- [ ] ...
- [ ] ...

## Technical notes
Implementation guidance, constraints, related models, or API details.

## Out of scope
What should not be included in this issue.

## Linked tasks
- [ ] ...
- [ ] ...

## Linked bugs
- [ ] ...
```

## Suggested GitHub issue template for bugs

```md
## Bug summary
Short description.

## Expected behavior
What should happen.

## Actual behavior
What happens instead.

## Steps to reproduce
1. ...
2. ...
3. ...

## Environment
Branch, commit, local or CI, database version, Docker version.

## Impact
Why this matters.

## Related milestone/story
Link the milestone and story issue.
```

## Working rule

The roadmap should be treated as the top-level plan, but each milestone should be executed through user stories and tasks in GitHub Projects. That way the vision stays clear while daily work stays concrete and trackable.