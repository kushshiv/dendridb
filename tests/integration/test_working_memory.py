import asyncio
from uuid import UUID

import pytest

from dendridb.config import get_settings

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_and_list_working_memory_by_session(integration_client):
    create_response = await integration_client.post(
        "/working-memory",
        json={
            "namespace": "team-a",
            "session_id": "sess-1",
            "key": "context",
            "content": "active task context",
            "task_id": "task-9",
            "ttl_seconds": 3600,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["session_id"] == "sess-1"
    assert created["key"] == "context"
    assert created["expires_at"] is not None

    await integration_client.post(
        "/working-memory",
        json={
            "namespace": "team-a",
            "session_id": "sess-2",
            "key": "context",
            "content": "other session",
        },
    )

    response = await integration_client.get(
        "/working-memory",
        params={"namespace": "team-a", "session_id": "sess-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["content"] == "active task context"


@pytest.mark.asyncio
async def test_replace_working_memory_updates_same_session_key(integration_client):
    first = await integration_client.put(
        "/working-memory/replace",
        json={
            "namespace": "team-a",
            "session_id": "sess-1",
            "key": "context",
            "content": "version one",
        },
    )
    assert first.status_code == 200
    first_id = first.json()["id"]

    second = await integration_client.put(
        "/working-memory/replace",
        json={
            "namespace": "team-a",
            "session_id": "sess-1",
            "key": "context",
            "content": "version two",
        },
    )
    assert second.status_code == 200
    assert second.json()["id"] == first_id
    assert second.json()["content"] == "version two"


@pytest.mark.asyncio
async def test_patch_updates_working_memory(integration_client):
    create_response = await integration_client.post(
        "/working-memory",
        json={
            "namespace": "team-a",
            "session_id": "sess-1",
            "key": "notes",
            "content": "initial",
        },
    )
    item_id = create_response.json()["id"]

    patch_response = await integration_client.patch(
        f"/working-memory/{item_id}",
        json={"content": "patched", "ttl_seconds": 7200},
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["content"] == "patched"
    assert patched["ttl_seconds"] == 7200


@pytest.mark.asyncio
async def test_expired_working_memory_is_hidden(integration_client):
    settings = get_settings()
    create_response = await integration_client.post(
        "/working-memory",
        json={
            "namespace": "team-a",
            "session_id": "sess-expire",
            "key": "temp",
            "content": "will expire",
            "ttl_seconds": 1 if settings.working_memory_backend == "redis" else 3600,
        },
    )
    item_id = UUID(create_response.json()["id"])

    if settings.working_memory_backend == "redis":
        await asyncio.sleep(1.2)
    else:
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import text

        from dendridb.core.database import get_session_factory

        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(
                text(
                    "UPDATE working_memory_items SET expires_at = :expires_at WHERE id = :item_id"
                ),
                {
                    "expires_at": datetime.now(UTC) - timedelta(minutes=1),
                    "item_id": item_id,
                },
            )
            await session.commit()

    list_response = await integration_client.get(
        "/working-memory",
        params={"namespace": "team-a", "session_id": "sess-expire"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0

    get_response = await integration_client.get(f"/working-memory/{item_id}")
    assert get_response.status_code == 404

    include_response = await integration_client.get(
        f"/working-memory/{item_id}",
        params={"include_expired": True},
    )
    if settings.working_memory_backend == "redis":
        assert include_response.status_code == 404
    else:
        assert include_response.status_code == 200
