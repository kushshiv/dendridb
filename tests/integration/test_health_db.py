import os

import pytest
from httpx import ASGITransport, AsyncClient

from dendridb.api.main import create_app
from dendridb.core.database import check_database_connection


def _database_configured() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_database_connection():
    if not _database_configured():
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 with PostgreSQL running to enable")

    assert await check_database_connection() is True


@pytest.mark.asyncio
async def test_health_endpoint_with_database():
    if not _database_configured():
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 with PostgreSQL running to enable")

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["checks"]["database"] == "ok"
