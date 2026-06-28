"""Shared end-to-end memory flow exercised across all milestones."""

from __future__ import annotations

import uuid

from httpx import AsyncClient


async def run_full_memory_flow(client: AsyncClient, *, namespace: str | None = None) -> str:
    """Run the full DendriDB memory lifecycle over HTTP. Returns the namespace used."""
    ns = namespace or f"e2e-{uuid.uuid4().hex[:12]}"

    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json()["service"] == "DendriDB"

    live = await client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    ready = await client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    memory_a = await client.post(
        "/memories",
        json={
            "namespace": ns,
            "content": "User prefers dark mode for the dashboard",
            "salience": 0.9,
            "metadata": {"topic": "preferences"},
        },
    )
    assert memory_a.status_code == 201
    memory_a_id = memory_a.json()["id"]

    memory_b = await client.post(
        "/memories",
        json={
            "namespace": ns,
            "content": "Billing invoices are due on the first of the month",
            "salience": 0.8,
            "metadata": {"topic": "billing"},
        },
    )
    assert memory_b.status_code == 201
    memory_b_id = memory_b.json()["id"]

    memories = await client.get("/memories", params={"namespace": ns})
    assert memories.status_code == 200
    assert memories.json()["total"] >= 2

    working_memory = await client.put(
        "/working-memory/replace",
        json={
            "namespace": ns,
            "session_id": "e2e-session",
            "key": "current_task",
            "content": "Complete end-to-end onboarding flow",
            "ttl_seconds": 3600,
        },
    )
    assert working_memory.status_code == 200

    working_items = await client.get(
        "/working-memory",
        params={"namespace": ns, "session_id": "e2e-session"},
    )
    assert working_items.status_code == 200
    assert working_items.json()["total"] == 1

    episode = await client.post(
        "/episodes",
        json={
            "namespace": ns,
            "session_id": "e2e-session",
            "title": "Onboarding chat",
        },
    )
    assert episode.status_code == 201
    episode_id = episode.json()["id"]

    first_event = await client.post(
        f"/episodes/{episode_id}/events",
        json={"content": "User asked about pricing tiers"},
    )
    assert first_event.status_code == 201

    second_event = await client.post(
        f"/episodes/{episode_id}/events",
        json={"content": "User asked about annual billing discounts"},
    )
    assert second_event.status_code == 201

    replay = await client.get(f"/episodes/{episode_id}/replay")
    assert replay.status_code == 200
    assert len(replay.json()["events"]) == 2

    promote = await client.post(
        "/semantic-memory/promote",
        json={
            "namespace": ns,
            "key": "user-theme",
            "content": "User prefers dark mode for dashboards",
            "confidence": 0.9,
            "evidence": [{"source_type": "episode", "source_id": episode_id}],
        },
    )
    assert promote.status_code == 201

    semantic = await client.get(
        "/semantic-memory",
        params={"namespace": ns, "active_only": True},
    )
    assert semantic.status_code == 200
    assert semantic.json()["total"] >= 1

    association = await client.post(
        "/associations",
        json={
            "namespace": ns,
            "source_type": "memory_record",
            "source_id": memory_a_id,
            "target_type": "memory_record",
            "target_id": memory_b_id,
            "edge_type": "related",
            "weight": 0.7,
            "explanation": "Both relate to user account preferences",
        },
    )
    assert association.status_code == 201

    auto_link = await client.post(
        "/associations/auto-link",
        json={
            "namespace": ns,
            "metadata_match": True,
            "content_similarity": False,
        },
    )
    assert auto_link.status_code == 201

    related = await client.get(
        "/associations/related",
        params={
            "namespace": ns,
            "source_type": "memory_record",
            "source_id": memory_a_id,
            "depth": 2,
        },
    )
    assert related.status_code == 200
    assert len(related.json()["items"]) >= 1

    recall = await client.post(
        "/recall",
        json={
            "namespace": ns,
            "query": "dark mode dashboard preference",
            "limit": 5,
            "context_memory_id": memory_a_id,
        },
    )
    assert recall.status_code == 200
    recall_ids = {item["id"] for item in recall.json()["items"]}
    assert memory_a_id in recall_ids

    for index in range(2):
        consolidate_episode = await client.post(
            "/episodes",
            json={"namespace": ns, "session_id": f"consolidate-{index}"},
        )
        assert consolidate_episode.status_code == 201
        consolidate_episode_id = consolidate_episode.json()["id"]
        event = await client.post(
            f"/episodes/{consolidate_episode_id}/events",
            json={"content": "User prefers dark mode interface"},
        )
        assert event.status_code == 201

    consolidation = await client.post(
        "/consolidation/jobs",
        json={"namespace": ns, "min_pattern_occurrences": 2},
    )
    assert consolidation.status_code == 201
    assert consolidation.json()["status"] == "completed"
    assert consolidation.json()["stats"]["patterns_promoted"] >= 1

    ephemeral = await client.post(
        "/memories",
        json={
            "namespace": ns,
            "content": "Temporary note for lifecycle checks",
            "salience": 0.05,
        },
    )
    assert ephemeral.status_code == 201
    ephemeral_id = ephemeral.json()["id"]

    pinned = await client.post(f"/memories/{memory_a_id}/pin")
    assert pinned.status_code == 200
    assert pinned.json()["pinned"] is True

    archived = await client.post(f"/memories/{ephemeral_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["archived_at"] is not None

    active_only = await client.get("/memories", params={"namespace": ns, "active_only": True})
    assert active_only.status_code == 200
    active_ids = {item["id"] for item in active_only.json()["items"]}
    assert ephemeral_id not in active_ids

    restored = await client.post(f"/memories/{ephemeral_id}/restore")
    assert restored.status_code == 200
    assert restored.json()["archived_at"] is None

    decay = await client.post("/decay/jobs", json={"namespace": ns, "min_salience": 0.1})
    assert decay.status_code == 201
    assert decay.json()["status"] == "completed"

    recall_after_decay = await client.post(
        "/recall",
        json={"namespace": ns, "query": "billing invoice due date", "limit": 3},
    )
    assert recall_after_decay.status_code == 200
    assert len(recall_after_decay.json()["items"]) >= 1

    return ns
