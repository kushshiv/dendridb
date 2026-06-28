# Deployment Guide

## Docker Compose (recommended for local and small deployments)

```bash
cp .env.example .env
make docker-up-all
```

This starts:

- **postgres** — PostgreSQL 16 with pgvector
- **redis** — Redis 7 (working memory + Celery broker)
- **neo4j** — Neo4j 5 (association graph and traversal)
- **api** — FastAPI service on port 8000
- **worker** — Celery worker for consolidation and decay

For local development with hot reload:

```bash
make docker-up    # postgres + redis + neo4j
make migrate
make dev
```

## Health checks

- Liveness: `GET /health/live`
- Readiness: `GET /health/ready` (PostgreSQL + Redis + Neo4j)
- All three data services are required for a healthy deployment

## Production considerations

- Use strong credentials for PostgreSQL and Neo4j
- Set `ENVIRONMENT=production`, `DEBUG=false`, and `CELERY_TASK_ALWAYS_EAGER=false`
- Run migrations before starting the API: `alembic upgrade head`
- Run the Celery worker (`make worker` or Docker `worker` service)
- Place the API behind a reverse proxy with TLS
- Back up PostgreSQL and Neo4j volumes
- Monitor `/health/ready`

## Environment variables

See `.env.example`. Neo4j is required:

| Variable | Purpose |
|----------|---------|
| `NEO4J_URI` | Bolt URI (e.g. `bolt://neo4j:7687` in Docker) |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j credentials |

## Scaling

- Scale API instances horizontally; share PostgreSQL, Redis, and Neo4j
- Scale Celery workers for consolidation/decay throughput
- Neo4j holds the live association graph; PostgreSQL holds association records for CRUD
