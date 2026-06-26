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
```
