from typing import Any

from fastapi import APIRouter

from dendridb import __version__
from dendridb.config import get_settings
from dendridb.core.database import check_database_connection

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    """Return service health including database connectivity."""
    settings = get_settings()
    db_ok = await check_database_connection()
    status = "healthy" if db_ok else "degraded"
    return {
        "status": status,
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "checks": {
            "database": "ok" if db_ok else "unavailable",
        },
    }
