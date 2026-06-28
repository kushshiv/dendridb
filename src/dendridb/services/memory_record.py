from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.memory_record import MemoryRecordCreate
from dendridb.memory.visibility import is_active_memory
from dendridb.models.memory_record import MemoryRecord
from dendridb.services.recall import set_memory_embedding


class MemoryRecordFilters:
    def __init__(
        self,
        *,
        namespace: str | None = None,
        actor_id: str | None = None,
        memory_type: str | None = None,
        source: str | None = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        self.namespace = namespace
        self.actor_id = actor_id
        self.memory_type = memory_type
        self.source = source
        self.active_only = active_only
        self.limit = limit
        self.offset = offset


def _apply_filters(query, filters: MemoryRecordFilters):
    if filters.namespace is not None:
        query = query.where(MemoryRecord.namespace == filters.namespace)
    if filters.actor_id is not None:
        query = query.where(MemoryRecord.actor_id == filters.actor_id)
    if filters.memory_type is not None:
        query = query.where(MemoryRecord.memory_type == filters.memory_type)
    if filters.source is not None:
        query = query.where(MemoryRecord.source == filters.source)
    if filters.active_only:
        query = query.where(MemoryRecord.archived_at.is_(None))
    return query


def _filter_active_records(records: list[MemoryRecord]) -> list[MemoryRecord]:
    return [
        record
        for record in records
        if is_active_memory(metadata=record.metadata_, archived_at=record.archived_at)
    ]


async def create_memory_record(
    session: AsyncSession,
    payload: MemoryRecordCreate,
) -> MemoryRecord:
    record = MemoryRecord(
        namespace=payload.namespace,
        actor_id=payload.actor_id,
        memory_type=payload.memory_type,
        content=payload.content,
        metadata_=payload.metadata,
        source=payload.source,
        provenance=payload.provenance,
        confidence=payload.confidence,
        salience=payload.salience,
    )
    session.add(record)
    await session.flush()
    await set_memory_embedding(session, record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_memory_record(session: AsyncSession, record_id: UUID) -> MemoryRecord | None:
    return await session.get(MemoryRecord, record_id)


async def list_memory_records(
    session: AsyncSession,
    filters: MemoryRecordFilters,
) -> tuple[list[MemoryRecord], int]:
    base_query = select(MemoryRecord)
    filtered_query = _apply_filters(base_query, filters)

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = (
        _apply_filters(select(MemoryRecord), filters)
        .order_by(MemoryRecord.created_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )
    result = await session.execute(list_query)
    records = list(result.scalars().all())
    if filters.active_only:
        records = _filter_active_records(records)
    return records, total
