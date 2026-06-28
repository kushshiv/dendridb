import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_consolidation_promotes_repeated_episode_patterns(integration_client):
    for _ in range(2):
        episode_id = (
            await integration_client.post(
                "/episodes",
                json={"namespace": "team-a", "session_id": "sess-consolidate"},
            )
        ).json()["id"]
        await integration_client.post(
            f"/episodes/{episode_id}/events",
            json={"content": "User prefers dark mode interface"},
        )

    response = await integration_client.post(
        "/consolidation/jobs",
        json={
            "namespace": "team-a",
            "min_pattern_occurrences": 2,
            "lookback_hours": 168,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["stats"]["episodes_replayed"] == 2
    assert payload["stats"]["patterns_promoted"] == 1

    semantic = await integration_client.get(
        "/semantic-memory",
        params={"namespace": "team-a", "active_only": True},
    )
    assert semantic.status_code == 200
    assert semantic.json()["total"] == 1
    assert "dark mode" in semantic.json()["items"][0]["content"].lower()


@pytest.mark.asyncio
async def test_consolidation_merges_duplicate_memory_records(integration_client):
    keep = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Billing invoice timing question",
            "salience": 5.0,
        },
    )
    duplicate = await integration_client.post(
        "/memories",
        json={
            "namespace": "team-a",
            "content": "Billing invoice timing question",
            "salience": 0.5,
        },
    )

    response = await integration_client.post(
        "/consolidation/jobs",
        json={"namespace": "team-a", "duplicate_similarity_threshold": 0.8},
    )
    assert response.status_code == 201
    assert response.json()["stats"]["duplicates_merged"] == 1

    merged = await integration_client.get(f"/memories/{duplicate.json()['id']}")
    kept = await integration_client.get(f"/memories/{keep.json()['id']}")
    assert merged.json()["metadata"]["consolidation_status"] == "merged"
    assert merged.json()["metadata"]["merged_into"] == keep.json()["id"]
    assert kept.json()["salience"] == pytest.approx(5.1)


@pytest.mark.asyncio
async def test_consolidation_does_not_modify_episodes(integration_client):
    episode = await integration_client.post(
        "/episodes",
        json={"namespace": "team-a", "session_id": "sess-immutable", "summary": "Original"},
    )
    episode_id = episode.json()["id"]
    before = await integration_client.get(f"/episodes/{episode_id}")

    await integration_client.post(
        f"/episodes/{episode_id}/events",
        json={"content": "Repeated fact for consolidation"},
    )
    await integration_client.post(
        "/consolidation/jobs",
        json={"namespace": "team-a"},
    )

    after = await integration_client.get(f"/episodes/{episode_id}")
    assert after.json()["summary"] == before.json()["summary"]
    assert after.json()["updated_at"] == before.json()["updated_at"]


@pytest.mark.asyncio
async def test_repeated_consolidation_merges_semantic_duplicates(integration_client):
    for _ in range(2):
        episode_id = (
            await integration_client.post(
                "/episodes",
                json={"namespace": "team-a", "session_id": "sess-repeat"},
            )
        ).json()["id"]
        await integration_client.post(
            f"/episodes/{episode_id}/events",
            json={"content": "Finance team owns billing"},
        )

    first = await integration_client.post(
        "/consolidation/jobs",
        json={"namespace": "team-a", "min_pattern_occurrences": 2},
    )
    second = await integration_client.post(
        "/consolidation/jobs",
        json={"namespace": "team-a", "min_pattern_occurrences": 2},
    )
    assert first.json()["stats"]["patterns_promoted"] == 1
    assert second.json()["stats"]["patterns_promoted"] == 1
    assert "merged" in second.json()["stats"]["promotion_actions"]

    semantic = await integration_client.get(
        "/semantic-memory",
        params={"namespace": "team-a", "active_only": True},
    )
    assert semantic.json()["total"] == 1
