from typing import Any

from fastapi import APIRouter, HTTPException, status

from dendridb import __version__
from dendridb.config import get_settings
from dendridb.core.database import check_database_connection

router = APIRouter()


async def _database_check() -> dict[str, str]:
    db_ok = await check_database_connection()
    return {"database": "ok" if db_ok else "unavailable"}


@router.get("/health")
async def health() -> dict[str, Any]:
    """Return service health including database connectivity."""
    settings = get_settings()
    checks = await _database_check()
    db_ok = checks["database"] == "ok"
    return {
        "status": "healthy" if db_ok else "degraded",
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
    checks = await _database_check()
    if checks["database"] != "ok":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "checks": checks},
        )
    return {"status": "ready", "checks": checks}
