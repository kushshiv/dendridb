import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_episode_and_append_events(integration_client):
    episode_response = await integration_client.post(
        "/episodes",
        json={
            "namespace": "team-a",
            "session_id": "sess-ep-1",
            "task_id": "task-7",
            "actor_id": "user-1",
            "title": "Checkout flow",
            "metadata": {"channel": "web"},
        },
    )
    assert episode_response.status_code == 201
    episode = episode_response.json()
    episode_id = episode["id"]
    assert episode["event_count"] == 0

    first_event = await integration_client.post(
        f"/episodes/{episode_id}/events",
        json={
            "content": "Opened cart",
            "event_type": "view",
            "source": "frontend",
            "provenance": {"step": 1},
        },
    )
    assert first_event.status_code == 201
    assert first_event.json()["sequence_number"] == 0

    second_event = await integration_client.post(
        f"/episodes/{episode_id}/events",
        json={"content": "Applied coupon", "event_type": "action"},
    )
    assert second_event.status_code == 201
    assert second_event.json()["sequence_number"] == 1

    get_response = await integration_client.get(f"/episodes/{episode_id}")
    assert get_response.status_code == 200
    assert get_response.json()["event_count"] == 2


@pytest.mark.asyncio
async def test_replay_returns_events_in_order(integration_client):
    episode_id = (
        await integration_client.post(
            "/episodes",
            json={"namespace": "team-a", "session_id": "sess-replay"},
        )
    ).json()["id"]

    for content in ["alpha", "beta", "gamma"]:
        await integration_client.post(
            f"/episodes/{episode_id}/events",
            json={"content": content},
        )

    replay_response = await integration_client.get(f"/episodes/{episode_id}/replay")
    assert replay_response.status_code == 200
    payload = replay_response.json()
    assert payload["episode"]["event_count"] == 3
    assert [event["content"] for event in payload["events"]] == ["alpha", "beta", "gamma"]
    assert [event["sequence_number"] for event in payload["events"]] == [0, 1, 2]


@pytest.mark.asyncio
async def test_list_episodes_by_session(integration_client):
    await integration_client.post(
        "/episodes",
        json={"namespace": "team-a", "session_id": "sess-a", "title": "A"},
    )
    await integration_client.post(
        "/episodes",
        json={"namespace": "team-a", "session_id": "sess-b", "title": "B"},
    )

    response = await integration_client.get(
        "/episodes",
        params={"namespace": "team-a", "session_id": "sess-a"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["title"] == "A"


@pytest.mark.asyncio
async def test_append_to_missing_episode_returns_404(integration_client):
    response = await integration_client.post(
        "/episodes/00000000-0000-0000-0000-000000000099/events",
        json={"content": "orphan event"},
    )
    assert response.status_code == 404
