"""Redis-backed working memory with native TTL support."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from dendridb.api.schemas.working_memory import (
    WorkingMemoryCreate,
    WorkingMemoryReplace,
    WorkingMemoryUpdate,
)
from dendridb.core.redis_client import WORKING_MEMORY_KEY_PREFIX, get_redis_client
from dendridb.memory.expiry import compute_expires_at, is_expired
from dendridb.working_memory.filters import WorkingMemoryFilters
from dendridb.working_memory.record import WorkingMemoryConflictError, WorkingMemoryRecord


def _item_key(item_id: UUID) -> str:
    return f"{WORKING_MEMORY_KEY_PREFIX}item:{item_id}"


def _lookup_key(namespace: str, session_id: str, key: str) -> str:
    return f"{WORKING_MEMORY_KEY_PREFIX}lookup:{namespace}:{session_id}:{key}"


def _session_index_key(namespace: str, session_id: str) -> str:
    return f"{WORKING_MEMORY_KEY_PREFIX}idx:{namespace}:{session_id}"


def _namespace_index_key(namespace: str) -> str:
    return f"{WORKING_MEMORY_KEY_PREFIX}ns:{namespace}"


def _record_to_payload(record: WorkingMemoryRecord) -> str:
    return json.dumps(
        {
            "id": str(record.id),
            "namespace": record.namespace,
            "session_id": record.session_id,
            "task_id": record.task_id,
            "key": record.key,
            "actor_id": record.actor_id,
            "content": record.content,
            "metadata": record.metadata_,
            "ttl_seconds": record.ttl_seconds,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }
    )


def _payload_to_record(payload: str) -> WorkingMemoryRecord | None:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return WorkingMemoryRecord(
        id=UUID(data["id"]),
        namespace=data["namespace"],
        session_id=data["session_id"],
        task_id=data.get("task_id"),
        key=data["key"],
        actor_id=data.get("actor_id"),
        content=data["content"],
        metadata_=data.get("metadata") or {},
        ttl_seconds=data.get("ttl_seconds"),
        expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )


def _build_record(
    payload: WorkingMemoryCreate | WorkingMemoryReplace,
    *,
    item_id: UUID | None = None,
    created_at: datetime | None = None,
) -> WorkingMemoryRecord:
    now = datetime.now(UTC)
    return WorkingMemoryRecord(
        id=item_id or uuid4(),
        namespace=payload.namespace,
        session_id=payload.session_id,
        task_id=payload.task_id,
        key=payload.key,
        actor_id=payload.actor_id,
        content=payload.content,
        metadata_=payload.metadata,
        ttl_seconds=payload.ttl_seconds,
        expires_at=compute_expires_at(payload.ttl_seconds, from_time=now),
        created_at=created_at or now,
        updated_at=now,
    )


async def _store_record(record: WorkingMemoryRecord) -> WorkingMemoryRecord:
    client = get_redis_client()
    lookup = _lookup_key(record.namespace, record.session_id, record.key)
    item_key = _item_key(record.id)
    payload = _record_to_payload(record)

    existing_lookup = await client.get(lookup)
    if existing_lookup is not None and existing_lookup != str(record.id):
        raise WorkingMemoryConflictError("Working memory key already exists for this session")

    pipe = client.pipeline()
    pipe.set(item_key, payload)
    pipe.set(lookup, str(record.id))
    pipe.sadd(_session_index_key(record.namespace, record.session_id), str(record.id))
    pipe.sadd(_namespace_index_key(record.namespace), str(record.id))
    if record.ttl_seconds is not None:
        pipe.expire(item_key, record.ttl_seconds)
        pipe.expire(lookup, record.ttl_seconds)
    await pipe.execute()
    return record


async def create_working_memory_item(payload: WorkingMemoryCreate) -> WorkingMemoryRecord:
    client = get_redis_client()
    lookup = _lookup_key(payload.namespace, payload.session_id, payload.key)
    if await client.exists(lookup):
        raise WorkingMemoryConflictError("Working memory key already exists for this session")
    record = _build_record(payload)
    return await _store_record(record)


async def replace_working_memory_item(payload: WorkingMemoryReplace) -> WorkingMemoryRecord:
    client = get_redis_client()
    lookup = _lookup_key(payload.namespace, payload.session_id, payload.key)
    now = datetime.now(UTC)
    existing_id = await client.get(lookup)
    if existing_id:
        existing = await get_working_memory_item(UUID(existing_id), include_expired=True)
        if existing is not None and not is_expired(existing.expires_at, now=now):
            record = WorkingMemoryRecord(
                id=existing.id,
                namespace=payload.namespace,
                session_id=payload.session_id,
                task_id=payload.task_id,
                key=payload.key,
                actor_id=payload.actor_id,
                content=payload.content,
                metadata_=payload.metadata,
                ttl_seconds=payload.ttl_seconds,
                expires_at=compute_expires_at(payload.ttl_seconds, from_time=now),
                created_at=existing.created_at,
                updated_at=now,
            )
            return await _store_record(record)

    record = _build_record(payload)
    return await _store_record(record)


async def get_working_memory_item(
    item_id: UUID,
    *,
    include_expired: bool = False,
    now: datetime | None = None,
) -> WorkingMemoryRecord | None:
    client = get_redis_client()
    payload = await client.get(_item_key(item_id))
    if payload is None:
        return None
    record = _payload_to_record(payload)
    if record is None:
        return None
    current = now or datetime.now(UTC)
    if not include_expired and is_expired(record.expires_at, now=current):
        return None
    return record


async def update_working_memory_item(
    item_id: UUID,
    payload: WorkingMemoryUpdate,
) -> WorkingMemoryRecord | None:
    record = await get_working_memory_item(item_id)
    if record is None:
        return None

    now = datetime.now(UTC)
    updated = WorkingMemoryRecord(
        id=record.id,
        namespace=record.namespace,
        session_id=record.session_id,
        task_id=payload.task_id if payload.task_id is not None else record.task_id,
        key=record.key,
        actor_id=payload.actor_id if payload.actor_id is not None else record.actor_id,
        content=payload.content if payload.content is not None else record.content,
        metadata_=payload.metadata if payload.metadata is not None else record.metadata_,
        ttl_seconds=payload.ttl_seconds if payload.ttl_seconds is not None else record.ttl_seconds,
        expires_at=record.expires_at,
        created_at=record.created_at,
        updated_at=now,
    )
    if payload.ttl_seconds is not None:
        updated = WorkingMemoryRecord(
            id=updated.id,
            namespace=updated.namespace,
            session_id=updated.session_id,
            task_id=updated.task_id,
            key=updated.key,
            actor_id=updated.actor_id,
            content=updated.content,
            metadata_=updated.metadata_,
            ttl_seconds=updated.ttl_seconds,
            expires_at=compute_expires_at(payload.ttl_seconds, from_time=now),
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
    return await _store_record(updated)


async def _collect_item_ids(filters: WorkingMemoryFilters) -> set[str]:
    client = get_redis_client()
    if filters.namespace is not None and filters.session_id is not None:
        return set(await client.smembers(_session_index_key(filters.namespace, filters.session_id)))
    if filters.namespace is not None:
        return set(await client.smembers(_namespace_index_key(filters.namespace)))
    ids: set[str] = set()
    async for key in client.scan_iter(match=f"{WORKING_MEMORY_KEY_PREFIX}item:*"):
        ids.add(key.rsplit(":", 1)[-1])
    return ids


async def list_working_memory_items(
    filters: WorkingMemoryFilters,
) -> tuple[list[WorkingMemoryRecord], int]:
    item_ids = await _collect_item_ids(filters)
    records: list[WorkingMemoryRecord] = []
    for item_id in item_ids:
        record = await get_working_memory_item(
            UUID(item_id),
            include_expired=filters.include_expired,
            now=filters.now,
        )
        if record is None:
            continue
        if filters.namespace is not None and record.namespace != filters.namespace:
            continue
        if filters.session_id is not None and record.session_id != filters.session_id:
            continue
        if filters.task_id is not None and record.task_id != filters.task_id:
            continue
        records.append(record)

    records.sort(key=lambda item: item.updated_at, reverse=True)
    total = len(records)
    page = records[filters.offset : filters.offset + filters.limit]
    return page, total
