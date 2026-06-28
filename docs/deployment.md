# Deployment Guide

## Docker Compose (recommended for local and small deployments)

```bash
cp .env.example .env
# Edit .env for production credentials
make docker-up-all
```

This starts:

- **postgres** — PostgreSQL 16 with pgvector on port 5432
- **api** — DendriDB FastAPI service on port 8000

For local development with hot reload, use `make docker-up` (Postgres only) and `make dev` instead.

## Health checks

- API: `GET /health`
- Docker Compose includes health checks for both services

## Production considerations

- Use strong `POSTGRES_PASSWORD` values
- Set `ENVIRONMENT=production` and `DEBUG=false`
- Run migrations before starting the API: `alembic upgrade head`
- Place the API behind a reverse proxy with TLS
- Configure backups for PostgreSQL volumes
- Monitor `/health` for database connectivity

## Environment variables

Production deployments should set all database variables explicitly. Do not rely on defaults.

## Scaling

The API runs as a single process by default. Consolidation and decay jobs can be triggered via the API or CLI (`dendridb consolidate run`, `dendridb decay run`). Horizontal scaling of the API requires shared PostgreSQL and careful session handling. For heavier workloads, run job commands on a schedule or as separate worker processes pointing at the same database.
