# API Guide

## Base URL

Local development: `http://localhost:8000`

## Endpoints

### `GET /health`

Returns service health and database connectivity status.

**Response**

```json
{
  "status": "healthy",
  "service": "DendriDB",
  "version": "0.1.0",
  "environment": "development",
  "checks": {
    "database": "ok"
  }
}
```

| Field | Description |
|-------|-------------|
| `status` | `healthy` when database is reachable, `degraded` otherwise |
| `service` | Application name |
| `version` | Installed DendriDB version |
| `environment` | Current environment (`development`, `test`, `production`) |
| `checks.database` | `ok` or `unavailable` |

### `GET /health/live`

Process liveness probe. Returns `200 OK` with `{"status": "alive"}` when the API process is running.

### `GET /health/ready`

Readiness probe for orchestrators. Returns `200 OK` when PostgreSQL is reachable, or `503 Service Unavailable` when the database check fails.

### `POST /memories`

Create a memory record.

**Request body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Tenant or namespace for isolation |
| `content` | string | yes | Memory content |
| `actor_id` | string | no | Creator or subject identifier |
| `memory_type` | string | no | Defaults to `generic` |
| `metadata` | object | no | Arbitrary JSON metadata |
| `source` | string | no | Origin of the memory (e.g. `chat`, `api`) |
| `provenance` | object | no | Traceability details |
| `confidence` | float | no | 0.0–1.0 |
| `salience` | float | no | Importance score (≥ 0) |

**Example**

```json
{
  "namespace": "team-a",
  "content": "User prefers dark mode",
  "actor_id": "user-42",
  "source": "onboarding",
  "metadata": {"category": "preference"},
  "provenance": {"channel": "web"}
}
```

**Response:** `201 Created` with the stored record.

Memory records include `pinned`, `archived_at`, and `last_retrieved_at` lifecycle fields. Embeddings are generated automatically on create.

### `GET /memories/{record_id}`

Retrieve a single memory record by UUID.

**Response:** `200 OK` with the record, or `404 Not Found` if missing.

### `GET /memories`

List memory records with optional filters and pagination.

**Query parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | string | Filter by namespace |
| `actor_id` | string | Filter by actor |
| `memory_type` | string | Filter by memory type |
| `source` | string | Filter by source |
| `active_only` | boolean | Exclude archived and merged records (default `true`) |
| `limit` | int | Page size (1–200, default 50) |
| `offset` | int | Offset (default 0) |

**Response**

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

### `POST /memories/{record_id}/pin`

Pin a memory so decay jobs skip it. Returns `404` if the record is missing or archived.

### `POST /memories/{record_id}/unpin`

Remove the pin from a memory record.

### `POST /memories/{record_id}/archive`

Soft-archive a memory (sets `archived_at`). Archived records are excluded from recall and active listings.

### `POST /memories/{record_id}/restore`

Restore an archived memory back to active status.

## Working memory

Short-term, session-scoped memory with TTL and replace support.

### `POST /working-memory`

Create a working memory item. Returns `409 Conflict` if the same `namespace` + `session_id` + `key` already exists — use `PUT /working-memory/replace` instead.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Tenant or namespace |
| `session_id` | string | yes | Session scope |
| `key` | string | yes | Item key within the session |
| `content` | string | yes | Memory content |
| `task_id` | string | no | Optional task scope |
| `actor_id` | string | no | Actor identifier |
| `metadata` | object | no | Arbitrary JSON metadata |
| `ttl_seconds` | int | no | Time-to-live in seconds |

### `PUT /working-memory/replace`

Create or update (upsert) working memory for a `namespace` + `session_id` + `key`. Refreshes TTL on update.

### `GET /working-memory/{item_id}`

Retrieve a working memory item. Expired items return `404` unless `include_expired=true`.

### `PATCH /working-memory/{item_id}`

Update content, metadata, task, actor, or TTL for an active (non-expired) item.

### `GET /working-memory`

List working memory with session/task filters. Expired items are excluded by default.

| Parameter | Type | Description |
|-----------|------|-------------|
| `namespace` | string | Filter by namespace |
| `session_id` | string | Filter by session |
| `task_id` | string | Filter by task |
| `include_expired` | bool | Include expired items (default false) |
| `limit` | int | Page size (1–200, default 50) |
| `offset` | int | Offset (default 0) |

## Episodic memory

Store ordered sequences of events grouped into episodes.

### `POST /episodes`

Create an episode with session/task context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Tenant or namespace |
| `session_id` | string | yes | Session grouping |
| `task_id` | string | no | Task context |
| `actor_id` | string | no | Actor identifier |
| `title` | string | no | Episode title |
| `summary` | string | no | Episode summary |
| `metadata` | object | no | Arbitrary JSON metadata |

### `POST /episodes/{episode_id}/events`

Append an event to an episode. Events receive sequential `sequence_number` values starting at `0`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | yes | Event content |
| `event_type` | string | no | Defaults to `event` |
| `metadata` | object | no | Arbitrary JSON metadata |
| `source` | string | no | Event source |
| `provenance` | object | no | Traceability details |

### `GET /episodes/{episode_id}/replay`

Return the episode and all events in sequence order (for replay/consolidation).

### `GET /episodes/{episode_id}`

Retrieve episode metadata including `event_count`.

### `GET /episodes`

List episodes with optional filters: `namespace`, `session_id`, `task_id`, `actor_id`.

### `POST /semantic-memory`

Create a semantic memory directly. Returns `409` if an active record already exists for the same `namespace` + `key`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Tenant or namespace |
| `key` | string | yes | Stable fact identifier within namespace |
| `content` | string | yes | Fact content |
| `confidence` | float | no | 0.0–1.0, defaults to `0.5` |
| `actor_id` | string | no | Actor identifier |
| `source` | string | no | Origin of the fact |
| `metadata` | object | no | Arbitrary JSON metadata |
| `provenance` | object | no | Traceability details |
| `evidence` | array | no | Links to supporting sources |

Each evidence item:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_type` | string | yes | `memory_record`, `episode`, or `episodic_event` |
| `source_id` | UUID | yes | ID of the supporting record |

### `POST /semantic-memory/promote`

Promote knowledge into semantic memory with merge/version rules:

- **created** — no active fact for the key
- **merged** — same content; confidence increases, evidence links deduplicated
- **versioned** — conflicting content; old record marked `superseded`, new version created

Request body matches `POST /semantic-memory`.

### `GET /semantic-memory/{memory_id}`

Retrieve a semantic memory including `evidence_count`, `version`, and `status`.

### `GET /semantic-memory/{memory_id}/evidence`

List evidence links for a semantic memory.

### `GET /semantic-memory`

List semantic memories with optional filters: `namespace`, `key`, `actor_id`, `active_only` (default `true`).

### `POST /associations`

Create a directed association between two memory nodes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Tenant or namespace |
| `source_type` | string | yes | `memory_record`, `episode`, `episodic_event`, or `semantic_memory` |
| `source_id` | UUID | yes | Source node ID |
| `target_type` | string | yes | Target node type |
| `target_id` | UUID | yes | Target node ID |
| `edge_type` | string | no | Defaults to `related` |
| `weight` | float | no | 0.0–1.0, defaults to `0.5` |
| `explanation` | string | no | Human-readable link reason |
| `metadata` | object | no | Arbitrary JSON metadata |

### `POST /associations/auto-link`

Automatically create association edges using metadata overlap and/or token-based content similarity.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Namespace to scan |
| `source_type` | string | no | Limit to one source node |
| `source_id` | UUID | no | Source node ID when scoped |
| `metadata_match` | boolean | no | Defaults to `true` |
| `content_similarity` | boolean | no | Defaults to `true` |
| `similarity_threshold` | float | no | Defaults to `0.3` |
| `limit` | integer | no | Max links per source, defaults to `20` |

### `GET /associations/related`

Retrieve related memories from a starting node. Results are ordered by path weight and include relationship explanations.

Query params: `namespace`, `source_type`, `source_id`, `depth` (default `1`), `min_weight` (default `0.1`), `limit`.

### `GET /associations/{association_id}`

Retrieve one association edge.

### `GET /associations`

List associations with optional filters: `namespace`, `source_type`, `source_id`, `target_type`, `target_id`, `edge_type`.

### `POST /recall`

Hybrid memory recall combining semantic similarity, recency, salience, and optional association context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Namespace to search |
| `query` | string | yes | Natural-language recall cue |
| `limit` | integer | no | Max results, defaults to `10` |
| `candidate_limit` | integer | no | Vector candidates to score, defaults to `100` |
| `context_memory_id` | UUID | no | Boost memories linked to this record |
| `min_score` | float | no | Minimum hybrid score, defaults to `0.0` |
| `weights` | object | no | Ranking weights for similarity, recency, salience, association |

Each result includes a hybrid `score` and an `explanation` with factor values, weighted contributions, and a summary.

Memory records receive embeddings automatically on create. Successful recall strengthens salience and updates `last_retrieved_at`. Archived and merged records are excluded from recall.

### `POST /recall/reindex`

Backfill embeddings for memories in a namespace.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Namespace to reindex |
| `limit` | integer | no | Max records, defaults to `500` |

### `POST /consolidation/jobs`

Run a consolidation job: replay recent episodes, merge duplicate memories, and promote repeated patterns into semantic memory.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Namespace to consolidate |
| `lookback_hours` | integer | no | Episode replay window, defaults to `168` |
| `duplicate_similarity_threshold` | float | no | Defaults to `0.85` |
| `min_pattern_occurrences` | integer | no | Minimum repeated events to promote, defaults to `2` |
| `dry_run` | boolean | no | Simulate without writes, defaults to `false` |

Episodes are replayed read-only. Duplicate memory records are marked `consolidation_status: merged` and excluded from recall.

### `GET /consolidation/jobs/{job_id}`

Retrieve consolidation job status and stats.

### `GET /consolidation/jobs`

List consolidation jobs with optional `namespace` filter.

### `POST /decay/jobs`

Run a decay job: apply salience decay based on time since last retrieval and archive memories below the minimum salience threshold.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | string | yes | Namespace to decay |
| `half_life_hours` | float | no | Salience half-life, defaults to `168` |
| `min_salience` | float | no | Archive threshold, defaults to `0.1` |
| `dry_run` | boolean | no | Simulate without writes, defaults to `false` |

Pinned memories are skipped. Merged and already-archived records are ignored.

### `GET /decay/jobs/{job_id}`

Retrieve decay job status and stats.

### `GET /decay/jobs`

List decay jobs with optional `namespace` filter.

## Interactive docs

When running locally:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Example usage

```bash
# Create a memory
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","content":"Hello from DendriDB"}'

# List memories in a namespace
curl "http://localhost:8000/memories?namespace=demo"

# Get by ID
curl http://localhost:8000/memories/<record-id>

# Working memory: upsert session context
curl -X PUT http://localhost:8000/working-memory/replace \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","session_id":"sess-1","key":"context","content":"Current task","ttl_seconds":3600}'

# List active working memory for a session
curl "http://localhost:8000/working-memory?namespace=demo&session_id=sess-1"

# Episodic memory: create episode and append events
curl -X POST http://localhost:8000/episodes \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","session_id":"sess-1","title":"Support chat"}'

curl -X POST http://localhost:8000/episodes/<episode-id>/events \
  -H "Content-Type: application/json" \
  -d '{"content":"User asked about billing","source":"chat","provenance":{"turn":1}}'

curl http://localhost:8000/episodes/<episode-id>/replay

# Semantic memory: promote a durable fact with episode evidence
curl -X POST http://localhost:8000/semantic-memory/promote \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","key":"user-theme","content":"User prefers dark mode","confidence":0.85,"evidence":[{"source_type":"episode","source_id":"<episode-id>"}]}'

curl "http://localhost:8000/semantic-memory?namespace=demo&active_only=true"

# Associations: link memories and fetch related context
curl -X POST http://localhost:8000/associations \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","source_type":"memory_record","source_id":"<id-a>","target_type":"memory_record","target_id":"<id-b>","edge_type":"supports","weight":0.9,"explanation":"Both mention billing policy"}'

curl -X POST http://localhost:8000/associations/auto-link \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","metadata_match":true,"content_similarity":true,"similarity_threshold":0.3}'

curl "http://localhost:8000/associations/related?namespace=demo&source_type=memory_record&source_id=<id-a>&depth=2"

# Hybrid recall with explainable ranking
curl -X POST http://localhost:8000/recall \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","query":"billing invoice question","limit":5,"weights":{"similarity":0.5,"recency":0.2,"salience":0.2,"association":0.1}}'

# Consolidation: replay episodes and promote repeated patterns
curl -X POST http://localhost:8000/consolidation/jobs \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","lookback_hours":168,"min_pattern_occurrences":2}'

# Or via CLI
dendridb consolidate run --namespace demo

# Decay: archive low-salience memories
curl -X POST http://localhost:8000/decay/jobs \
  -H "Content-Type: application/json" \
  -d '{"namespace":"demo","min_salience":0.1}'

curl -X POST http://localhost:8000/memories/<record-id>/pin

# Or via CLI
dendridb decay run --namespace demo
```
