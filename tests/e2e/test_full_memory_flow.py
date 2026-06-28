import os

import pytest
from tests.helpers.e2e_flow import run_full_memory_flow

pytestmark = pytest.mark.e2e


def _e2e_configured() -> bool:
    return os.getenv("RUN_E2E_TESTS", "0") == "1"


@pytest.mark.asyncio
async def test_full_memory_flow(e2e_client):
    namespace = await run_full_memory_flow(e2e_client)
    assert namespace.startswith("e2e-")


@pytest.mark.asyncio
async def test_live_health_endpoint():
    if not _e2e_configured() or os.getenv("E2E_LIVE", "0") != "1":
        pytest.skip("Set RUN_E2E_TESTS=1 and E2E_LIVE=1 with the API running to enable")

    from httpx import AsyncClient

    from conftest import e2e_base_url, wait_for_live_api

    base_url = e2e_base_url()
    await wait_for_live_api(base_url)
    async with AsyncClient(base_url=base_url, timeout=10.0) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "DendriDB"
