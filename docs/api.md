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

## Interactive docs

When running locally:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Future endpoints

Memory record APIs will be added in Milestone 1.
