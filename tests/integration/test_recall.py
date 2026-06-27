import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_recall_returns_semantically_similar_memories(integration_client):
    await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Customer asked about billing invoice timing"},
    )
    target = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Invoice billing cycle question from customer"},
    )
    await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "User prefers dark mode dashboard theme"},
    )

    response = await integration_client.post(
        "/recall",
        json={
            "namespace": "team-a",
            "query": "billing invoice question",
            "limit": 2,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_candidates"] >= 2
    assert payload["items"][0]["id"] == target.json()["id"]
    assert payload["items"][0]["explanation"]["summary"]
    assert "similarity" in payload["items"][0]["explanation"]["factors"]


@pytest.mark.asyncio
async def test_recall_salience_weight_affects_ranking(integration_client):
    await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Project alpha billing workflow notes",
            "salience": 0.1,
        },
    )
    similar_b = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Project alpha billing workflow summary",
            "salience": 10.0,
        },
    )

    response = await integration_client.post(
        "/recall",
        json={
            "namespace": "team-a",
            "query": "project alpha billing workflow",
            "limit": 2,
            "weights": {
                "similarity": 0.2,
                "recency": 0.1,
                "salience": 0.7,
                "association": 0.0,
            },
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["id"] == similar_b.json()["id"]
    assert (
        items[0]["explanation"]["contributions"]["salience"]
        >= items[1]["explanation"]["contributions"]["salience"]
    )


@pytest.mark.asyncio
async def test_recall_association_context_boosts_linked_memory(integration_client):
    context = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Context memory about support queue"},
    )
    linked = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Linked memory about escalation policy"},
    )
    await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Unrelated memory about office plants"},
    )

    await integration_client.post(
        "/associations",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": context.json()["id"],
            "target_type": "memory_record",
            "target_id": linked.json()["id"],
            "edge_type": "supports",
            "weight": 0.95,
            "explanation": "Escalation policy supports queue handling",
        },
    )

    response = await integration_client.post(
        "/recall",
        json={
            "namespace": "team-a",
            "query": "support queue escalation",
            "limit": 3,
            "context_memory_id": context.json()["id"],
            "weights": {
                "similarity": 0.2,
                "recency": 0.1,
                "salience": 0.1,
                "association": 0.6,
            },
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    linked_item = next(item for item in items if item["id"] == linked.json()["id"])
    assert linked_item["explanation"]["factors"]["association"] == 0.95
    assert "association" in linked_item["explanation"]["summary"].lower()


@pytest.mark.asyncio
async def test_reindex_backfills_embeddings(integration_client):
    response = await integration_client.post(
        "/recall/reindex",
        json={"namespace": "team-a", "limit": 10},
    )
    assert response.status_code == 200
    assert response.json()["namespace"] == "team-a"
