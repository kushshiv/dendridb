from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.working_memory import (
    WorkingMemoryCreate,
    WorkingMemoryReplace,
    WorkingMemoryUpdate,
)
from dendridb.memory.expiry import compute_expires_at, is_expired
from dendridb.models.working_memory import WorkingMemoryItem


class WorkingMemoryFilters:
    def __init__(
        self,
        *,
        namespace: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        include_expired: bool = False,
        limit: int = 50,
        offset: int = 0,
        now: datetime | None = None,
    ) -> None:
        self.namespace = namespace
        self.session_id = session_id
        self.task_id = task_id
        self.include_expired = include_expired
        self.limit = limit
        self.offset = offset
        self.now = now or datetime.now(UTC)


def _active_only_clause(now: datetime):
    return or_(
        WorkingMemoryItem.expires_at.is_(None),
        WorkingMemoryItem.expires_at > now,
    )


def _apply_filters(query, filters: WorkingMemoryFilters):
    if filters.namespace is not None:
        query = query.where(WorkingMemoryItem.namespace == filters.namespace)
    if filters.session_id is not None:
        query = query.where(WorkingMemoryItem.session_id == filters.session_id)
    if filters.task_id is not None:
        query = query.where(WorkingMemoryItem.task_id == filters.task_id)
    if not filters.include_expired:
        query = query.where(_active_only_clause(filters.now))
    return query


def _item_from_create(payload: WorkingMemoryCreate | WorkingMemoryReplace) -> WorkingMemoryItem:
    now = datetime.now(UTC)
    return WorkingMemoryItem(
        namespace=payload.namespace,
        session_id=payload.session_id,
        task_id=payload.task_id,
        key=payload.key,
        actor_id=payload.actor_id,
        content=payload.content,
        metadata_=payload.metadata,
        ttl_seconds=payload.ttl_seconds,
        expires_at=compute_expires_at(payload.ttl_seconds, from_time=now),
    )


async def create_working_memory_item(
    session: AsyncSession,
    payload: WorkingMemoryCreate,
) -> WorkingMemoryItem:
    item = _item_from_create(payload)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def replace_working_memory_item(
    session: AsyncSession,
    payload: WorkingMemoryReplace,
) -> WorkingMemoryItem:
    now = datetime.now(UTC)
    query = select(WorkingMemoryItem).where(
        WorkingMemoryItem.namespace == payload.namespace,
        WorkingMemoryItem.session_id == payload.session_id,
        WorkingMemoryItem.key == payload.key,
    )
    result = await session.execute(query)
    existing = result.scalar_one_or_none()

    if existing is not None and not is_expired(existing.expires_at, now=now):
        existing.task_id = payload.task_id
        existing.actor_id = payload.actor_id
        existing.content = payload.content
        existing.metadata_ = payload.metadata
        existing.ttl_seconds = payload.ttl_seconds
        existing.expires_at = compute_expires_at(payload.ttl_seconds, from_time=now)
        await session.commit()
        await session.refresh(existing)
        return existing

    if existing is not None:
        await session.delete(existing)
        await session.flush()

    item = _item_from_create(payload)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def get_working_memory_item(
    session: AsyncSession,
    item_id: UUID,
    *,
    include_expired: bool = False,
    now: datetime | None = None,
) -> WorkingMemoryItem | None:
    item = await session.get(WorkingMemoryItem, item_id)
    if item is None:
        return None
    current = now or datetime.now(UTC)
    if not include_expired and is_expired(item.expires_at, now=current):
        return None
    return item


async def update_working_memory_item(
    session: AsyncSession,
    item_id: UUID,
    payload: WorkingMemoryUpdate,
) -> WorkingMemoryItem | None:
    item = await get_working_memory_item(session, item_id)
    if item is None:
        return None

    now = datetime.now(UTC)
    if payload.content is not None:
        item.content = payload.content
    if payload.task_id is not None:
        item.task_id = payload.task_id
    if payload.actor_id is not None:
        item.actor_id = payload.actor_id
    if payload.metadata is not None:
        item.metadata_ = payload.metadata
    if payload.ttl_seconds is not None:
        item.ttl_seconds = payload.ttl_seconds
        item.expires_at = compute_expires_at(payload.ttl_seconds, from_time=now)

    await session.commit()
    await session.refresh(item)
    return item


async def list_working_memory_items(
    session: AsyncSession,
    filters: WorkingMemoryFilters,
) -> tuple[list[WorkingMemoryItem], int]:
    filtered_query = _apply_filters(select(WorkingMemoryItem), filters)

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = (
        _apply_filters(select(WorkingMemoryItem), filters)
        .order_by(WorkingMemoryItem.updated_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )
    result = await session.execute(list_query)
    return list(result.scalars().all()), total
