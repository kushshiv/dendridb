import os

import pytest
from httpx import AsyncClient


def _e2e_configured() -> bool:
    return os.getenv("RUN_E2E_TESTS", "0") == "1"


pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_live_health_endpoint():
    if not _e2e_configured():
        pytest.skip("Set RUN_E2E_TESTS=1 with the API running to enable")

    base_url = os.getenv("E2E_BASE_URL", "http://localhost:8000")
    async with AsyncClient(base_url=base_url) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "DendriDB"
