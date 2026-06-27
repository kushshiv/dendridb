import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_semantic_memory_with_evidence(integration_client):
    episode_id = (
        await integration_client.post(
            "/episodes",
            json={"namespace": "team-a", "session_id": "sess-sem"},
        )
    ).json()["id"]

    response = await integration_client.post(
        "/semantic-memory",
        json={
            "namespace": "team-a",
            "key": "user-theme",
            "content": "User prefers dark mode",
            "confidence": 0.8,
            "evidence": [{"source_type": "episode", "source_id": episode_id}],
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["version"] == 1
    assert payload["status"] == "active"
    assert payload["evidence_count"] == 1

    evidence_response = await integration_client.get(f"/semantic-memory/{payload['id']}/evidence")
    assert evidence_response.status_code == 200
    assert len(evidence_response.json()["items"]) == 1
    assert evidence_response.json()["items"][0]["source_id"] == episode_id


@pytest.mark.asyncio
async def test_direct_create_conflicts_with_active_key(integration_client):
    body = {
        "namespace": "team-a",
        "key": "duplicate-key",
        "content": "First fact",
    }
    first = await integration_client.post("/semantic-memory", json=body)
    assert first.status_code == 201

    second = await integration_client.post("/semantic-memory", json=body)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_promote_creates_new_fact(integration_client):
    response = await integration_client.post(
        "/semantic-memory/promote",
        json={
            "namespace": "team-a",
            "key": "billing-contact",
            "content": "Billing contact is finance@example.com",
            "confidence": 0.7,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["action"] == "created"
    assert payload["memory"]["version"] == 1


@pytest.mark.asyncio
async def test_promote_merge_same_content(integration_client):
    episode_id = (
        await integration_client.post(
            "/episodes",
            json={"namespace": "team-a", "session_id": "sess-merge"},
        )
    ).json()["id"]
    body = {
        "namespace": "team-a",
        "key": "user-theme",
        "content": "User prefers dark mode",
        "confidence": 0.6,
        "evidence": [{"source_type": "episode", "source_id": episode_id}],
    }
    first = await integration_client.post("/semantic-memory/promote", json=body)
    assert first.status_code == 201
    memory_id = first.json()["memory"]["id"]

    second = await integration_client.post(
        "/semantic-memory/promote",
        json={
            **body,
            "confidence": 0.9,
        },
    )
    assert second.status_code == 201
    payload = second.json()
    assert payload["action"] == "merged"
    assert payload["memory"]["id"] == memory_id
    assert payload["memory"]["confidence"] == 0.9
    assert payload["memory"]["version"] == 1

    duplicate_promote = await integration_client.post("/semantic-memory/promote", json=body)
    assert duplicate_promote.status_code == 201
    assert duplicate_promote.json()["action"] == "merged"
    assert duplicate_promote.json()["memory"]["evidence_count"] == 1


@pytest.mark.asyncio
async def test_promote_versions_on_contradiction(integration_client):
    base = {
        "namespace": "team-a",
        "key": "user-theme",
        "content": "User prefers light mode",
        "confidence": 0.8,
    }
    first = await integration_client.post("/semantic-memory/promote", json=base)
    old_id = first.json()["memory"]["id"]

    second = await integration_client.post(
        "/semantic-memory/promote",
        json={
            **base,
            "content": "User prefers dark mode",
            "confidence": 0.75,
        },
    )
    assert second.status_code == 201
    payload = second.json()
    assert payload["action"] == "versioned"
    assert payload["memory"]["version"] == 2
    assert payload["memory"]["id"] != old_id

    old_memory = await integration_client.get(f"/semantic-memory/{old_id}")
    assert old_memory.status_code == 200
    assert old_memory.json()["status"] == "superseded"
    assert old_memory.json()["superseded_by_id"] == payload["memory"]["id"]


@pytest.mark.asyncio
async def test_list_active_only_excludes_superseded(integration_client):
    base = {
        "namespace": "team-a",
        "key": "shipping-policy",
        "content": "Free shipping over $50",
        "confidence": 0.7,
    }
    await integration_client.post("/semantic-memory/promote", json=base)
    await integration_client.post(
        "/semantic-memory/promote",
        json={**base, "content": "Free shipping over $75"},
    )

    active = await integration_client.get(
        "/semantic-memory",
        params={"namespace": "team-a", "key": "shipping-policy", "active_only": True},
    )
    assert active.status_code == 200
    assert active.json()["total"] == 1
    assert active.json()["items"][0]["content"] == "Free shipping over $75"

    all_versions = await integration_client.get(
        "/semantic-memory",
        params={"namespace": "team-a", "key": "shipping-policy", "active_only": False},
    )
    assert all_versions.status_code == 200
    assert all_versions.json()["total"] == 2
