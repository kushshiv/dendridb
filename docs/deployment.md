# Deployment Guide

## Docker Compose (recommended for local and small deployments)

```bash
cp .env.example .env
# Edit .env for production credentials
make docker-up
```

This starts:

- **postgres** — PostgreSQL 16 with pgvector on port 5432
- **api** — DendriDB FastAPI service on port 8000

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

Milestone 0 is a single-process API. Future milestones will add worker processes for consolidation. Horizontal scaling of the API will require shared PostgreSQL and careful session handling.
