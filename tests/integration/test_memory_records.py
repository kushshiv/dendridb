import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_and_get_memory_record(integration_client):
    create_response = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "User prefers dark mode",
            "actor_id": "user-42",
            "source": "onboarding",
            "metadata": {"category": "preference"},
            "provenance": {"channel": "web"},
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["namespace"] == "team-a"
    assert created["content"] == "User prefers dark mode"
    assert created["actor_id"] == "user-42"
    assert created["source"] == "onboarding"
    assert created["metadata"] == {"category": "preference"}
    assert created["provenance"] == {"channel": "web"}
    assert "id" in created
    assert "created_at" in created

    record_id = created["id"]
    get_response = await integration_client.get(f"/memories/{record_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == record_id
    assert fetched["content"] == "User prefers dark mode"


@pytest.mark.asyncio
async def test_get_missing_memory_record_returns_404(integration_client):
    response = await integration_client.get(
        "/memories/00000000-0000-0000-0000-000000000099",
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_memory_records_with_namespace_filter(integration_client):
    await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "first"},
    )
    await integration_client.post(
        "/memories",
        json={"namespace": "team-b", "content": "second"},
    )

    response = await integration_client.get("/memories", params={"namespace": "team-a"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["namespace"] == "team-a"


@pytest.mark.asyncio
async def test_list_memory_records_filter_by_source(integration_client):
    await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "from chat", "source": "chat"},
    )
    await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "from api", "source": "api"},
    )

    response = await integration_client.get(
        "/memories",
        params={"namespace": "team-a", "source": "chat"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["source"] == "chat"
