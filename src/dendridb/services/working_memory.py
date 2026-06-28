from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.working_memory import (
    WorkingMemoryCreate,
    WorkingMemoryReplace,
    WorkingMemoryUpdate,
)
from dendridb.config import get_settings
from dendridb.working_memory import postgres_store, redis_store
from dendridb.working_memory.filters import WorkingMemoryFilters
from dendridb.working_memory.record import WorkingMemoryRecord

__all__ = ["WorkingMemoryFilters"]


def _use_redis() -> bool:
    return get_settings().working_memory_backend == "redis"


async def create_working_memory_item(
    session: AsyncSession,
    payload: WorkingMemoryCreate,
) -> WorkingMemoryRecord:
    if _use_redis():
        return await redis_store.create_working_memory_item(payload)
    return await postgres_store.create_working_memory_item(session, payload)


async def replace_working_memory_item(
    session: AsyncSession,
    payload: WorkingMemoryReplace,
) -> WorkingMemoryRecord:
    if _use_redis():
        return await redis_store.replace_working_memory_item(payload)
    return await postgres_store.replace_working_memory_item(session, payload)


async def get_working_memory_item(
    session: AsyncSession,
    item_id: UUID,
    *,
    include_expired: bool = False,
) -> WorkingMemoryRecord | None:
    if _use_redis():
        return await redis_store.get_working_memory_item(item_id, include_expired=include_expired)
    return await postgres_store.get_working_memory_item(
        session,
        item_id,
        include_expired=include_expired,
    )


async def update_working_memory_item(
    session: AsyncSession,
    item_id: UUID,
    payload: WorkingMemoryUpdate,
) -> WorkingMemoryRecord | None:
    if _use_redis():
        return await redis_store.update_working_memory_item(item_id, payload)
    return await postgres_store.update_working_memory_item(session, item_id, payload)


async def list_working_memory_items(
    session: AsyncSession,
    filters: WorkingMemoryFilters,
) -> tuple[list[WorkingMemoryRecord], int]:
    if _use_redis():
        return await redis_store.list_working_memory_items(filters)
    return await postgres_store.list_working_memory_items(session, filters)
