import pytest
from httpx import ASGITransport, AsyncClient

from dendridb import __version__
from dendridb.api.main import create_app


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_endpoint_without_db():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "DendriDB"
    assert payload["version"] == __version__
    assert payload["environment"] in {"development", "test"}
    assert payload["status"] in {"healthy", "degraded"}
    assert "database" in payload["checks"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liveness_endpoint():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_readiness_endpoint_without_db():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/ready")

    assert response.status_code in {200, 503}
    if response.status_code == 200:
        assert response.json()["status"] == "ready"
