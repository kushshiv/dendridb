import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_manual_association(integration_client):
    first = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Billing policy updated"},
    )
    second = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Finance team owns billing"},
    )
    first_id = first.json()["id"]
    second_id = second.json()["id"]

    response = await integration_client.post(
        "/associations",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": first_id,
            "target_type": "memory_record",
            "target_id": second_id,
            "edge_type": "supports",
            "weight": 0.85,
            "explanation": "Both describe billing ownership",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["edge_type"] == "supports"
    assert payload["weight"] == 0.85


@pytest.mark.asyncio
async def test_auto_link_by_metadata(integration_client):
    first = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Customer asked about invoice timing",
            "metadata": {"topic": "billing", "channel": "chat"},
        },
    )
    second = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Different wording entirely",
            "metadata": {"topic": "billing", "priority": "high"},
        },
    )
    first_id = first.json()["id"]

    response = await integration_client.post(
        "/associations/auto-link",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": first_id,
            "metadata_match": True,
            "content_similarity": False,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert len(payload["created"]) >= 1
    assert payload["created"][0]["edge_type"] == "metadata_match"
    assert payload["created"][0]["target_id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_auto_link_by_content_similarity(integration_client):
    first = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "User prefers dark mode dashboard theme",
        },
    )
    second = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Dashboard theme preference is dark mode",
        },
    )
    first_id = first.json()["id"]

    response = await integration_client.post(
        "/associations/auto-link",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": first_id,
            "metadata_match": False,
            "content_similarity": True,
            "similarity_threshold": 0.2,
        },
    )
    assert response.status_code == 201
    created = response.json()["created"]
    assert any(item["target_id"] == second.json()["id"] for item in created)
    assert any(item["edge_type"] == "content_similar" for item in created)


@pytest.mark.asyncio
async def test_related_memories_ordered_by_weight(integration_client):
    source = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Source memory"},
    )
    strong = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Strongly related"},
    )
    weak = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Weakly related"},
    )
    source_id = source.json()["id"]

    await integration_client.post(
        "/associations",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": source_id,
            "target_type": "memory_record",
            "target_id": strong.json()["id"],
            "weight": 0.95,
            "explanation": "High confidence link",
        },
    )
    await integration_client.post(
        "/associations",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": source_id,
            "target_type": "memory_record",
            "target_id": weak.json()["id"],
            "weight": 0.2,
            "explanation": "Low confidence link",
        },
    )

    response = await integration_client.get(
        "/associations/related",
        params={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": source_id,
            "depth": 1,
            "min_weight": 0.1,
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["path_weight"] >= items[1]["path_weight"]
    assert items[0]["explanation"]
    assert items[0]["summary"]["content"] == "Strongly related"


@pytest.mark.asyncio
async def test_related_traversal_deduplicates(integration_client):
    source = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Source"},
    )
    middle = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Middle"},
    )
    end = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "End"},
    )
    source_id = source.json()["id"]
    middle_id = middle.json()["id"]
    end_id = end.json()["id"]

    for target_id, weight in [(middle_id, 0.8), (end_id, 0.7)]:
        await integration_client.post(
            "/associations",
            json={
                "namespace": "team-a",
                "source_type": "memory_record",
                "source_id": source_id,
                "target_type": "memory_record",
                "target_id": target_id,
                "weight": weight,
            },
        )
    await integration_client.post(
        "/associations",
        json={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": middle_id,
            "target_type": "memory_record",
            "target_id": end_id,
            "weight": 0.9,
        },
    )

    response = await integration_client.get(
        "/associations/related",
        params={
            "namespace": "team-a",
            "source_type": "memory_record",
            "source_id": source_id,
            "depth": 2,
            "min_weight": 0.1,
        },
    )
    assert response.status_code == 200
    end_items = [item for item in response.json()["items"] if item["node_id"] == end_id]
    assert len(end_items) == 1
