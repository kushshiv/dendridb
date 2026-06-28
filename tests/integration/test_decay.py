import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_decay_archives_low_salience_memories(integration_client):
    created = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Ephemeral note", "salience": 0.05},
    )
    assert created.status_code == 201
    record_id = created.json()["id"]

    response = await integration_client.post(
        "/decay/jobs",
        json={"namespace": "team-a", "min_salience": 0.1},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["stats"]["records_archived"] == 1

    fetched = await integration_client.get(f"/memories/{record_id}")
    assert fetched.status_code == 200
    assert fetched.json()["archived_at"] is not None


@pytest.mark.asyncio
async def test_pinned_memory_is_not_archived_by_decay(integration_client):
    created = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Important pinned note", "salience": 0.05},
    )
    record_id = created.json()["id"]

    pin_response = await integration_client.post(f"/memories/{record_id}/pin")
    assert pin_response.status_code == 200
    assert pin_response.json()["pinned"] is True

    decay_response = await integration_client.post(
        "/decay/jobs",
        json={"namespace": "team-a", "min_salience": 0.1},
    )
    assert decay_response.status_code == 201
    assert decay_response.json()["stats"]["records_skipped_pinned"] == 1
    assert decay_response.json()["stats"]["records_archived"] == 0

    fetched = await integration_client.get(f"/memories/{record_id}")
    assert fetched.json()["archived_at"] is None


@pytest.mark.asyncio
async def test_archive_restore_and_list_active_only(integration_client):
    active = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Still active", "salience": 1.0},
    )
    archived = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "To archive", "salience": 1.0},
    )
    archived_id = archived.json()["id"]

    archive_response = await integration_client.post(f"/memories/{archived_id}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["archived_at"] is not None

    list_active = await integration_client.get(
        "/memories",
        params={"namespace": "team-a", "active_only": True},
    )
    assert list_active.status_code == 200
    active_ids = {item["id"] for item in list_active.json()["items"]}
    assert active.json()["id"] in active_ids
    assert archived_id not in active_ids

    restore_response = await integration_client.post(f"/memories/{archived_id}/restore")
    assert restore_response.status_code == 200
    assert restore_response.json()["archived_at"] is None


@pytest.mark.asyncio
async def test_recall_strengthens_salience_and_excludes_archived(integration_client):
    active = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Billing invoice timing question",
            "salience": 0.5,
        },
    )
    archived = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Billing invoice timing question archived copy",
            "salience": 5.0,
        },
    )
    archived_id = archived.json()["id"]
    await integration_client.post(f"/memories/{archived_id}/archive")

    recall_response = await integration_client.post(
        "/recall",
        json={"namespace": "team-a", "query": "billing invoice", "limit": 5},
    )
    assert recall_response.status_code == 200
    results = recall_response.json()["items"]
    result_ids = {item["id"] for item in results}
    assert active.json()["id"] in result_ids
    assert archived_id not in result_ids

    refreshed = await integration_client.get(f"/memories/{active.json()['id']}")
    assert refreshed.json()["last_retrieved_at"] is not None
    assert refreshed.json()["salience"] == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_decay_dry_run_does_not_write(integration_client):
    created = await integration_client.post(
        "/memories",
        json={"namespace": "team-a", "content": "Dry run candidate", "salience": 0.05},
    )
    record_id = created.json()["id"]

    response = await integration_client.post(
        "/decay/jobs",
        json={"namespace": "team-a", "min_salience": 0.1, "dry_run": True},
    )
    assert response.status_code == 201
    assert response.json()["stats"]["records_archived"] == 1

    fetched = await integration_client.get(f"/memories/{record_id}")
    assert fetched.json()["archived_at"] is None
