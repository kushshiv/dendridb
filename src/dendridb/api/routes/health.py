from typing import Any

from fastapi import APIRouter, HTTPException, status

from dendridb import __version__
from dendridb.config import get_settings
from dendridb.core.database import check_database_connection
from dendridb.core.redis_client import check_redis_connection
from dendridb.graph.neo4j_store import check_neo4j_connection
from dendridb.services.job_dispatch import uses_celery_queue

router = APIRouter()


async def _dependency_checks() -> dict[str, str]:
    settings = get_settings()
    checks: dict[str, str] = {}

    db_ok = await check_database_connection()
    checks["database"] = "ok" if db_ok else "unavailable"

    if settings.working_memory_backend == "redis" or uses_celery_queue():
        redis_ok = await check_redis_connection()
        checks["redis"] = "ok" if redis_ok else "unavailable"

    neo4j_ok = await check_neo4j_connection()
    checks["neo4j"] = "ok" if neo4j_ok else "unavailable"

    return checks


@router.get("/health")
async def health() -> dict[str, Any]:
    """Return service health including dependency connectivity."""
    settings = get_settings()
    checks = await _dependency_checks()
    all_ok = all(value == "ok" for value in checks.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "checks": checks,
    }


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Return process liveness for orchestrators."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness() -> dict[str, Any]:
    """Return readiness; fails when required dependencies are unavailable."""
    checks = await _dependency_checks()
    if any(value != "ok" for value in checks.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )
    return {"status": "ready", "checks": checks}
