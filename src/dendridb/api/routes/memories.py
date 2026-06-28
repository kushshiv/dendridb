from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.memory_record import (
    MemoryRecordCreate,
    MemoryRecordListResponse,
    MemoryRecordResponse,
)
from dendridb.core.database import get_db_session
from dendridb.services.decay import archive_memory, pin_memory, restore_memory, unpin_memory
from dendridb.services.memory_record import (
    MemoryRecordFilters,
    create_memory_record,
    get_memory_record,
    list_memory_records,
)

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", response_model=MemoryRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: MemoryRecordCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordResponse:
    record = await create_memory_record(session, payload)
    return MemoryRecordResponse.model_validate(record)


@router.get("/{record_id}", response_model=MemoryRecordResponse)
async def get_memory(
    record_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordResponse:
    record = await get_memory_record(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record {record_id} not found",
        )
    return MemoryRecordResponse.model_validate(record)


@router.post("/{record_id}/pin", response_model=MemoryRecordResponse)
async def pin_memory_route(
    record_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordResponse:
    record = await pin_memory(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record {record_id} not found or archived",
        )
    return MemoryRecordResponse.model_validate(record)


@router.post("/{record_id}/unpin", response_model=MemoryRecordResponse)
async def unpin_memory_route(
    record_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordResponse:
    record = await unpin_memory(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record {record_id} not found",
        )
    return MemoryRecordResponse.model_validate(record)


@router.post("/{record_id}/archive", response_model=MemoryRecordResponse)
async def archive_memory_route(
    record_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordResponse:
    record = await archive_memory(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record {record_id} not found or already archived",
        )
    return MemoryRecordResponse.model_validate(record)


@router.post("/{record_id}/restore", response_model=MemoryRecordResponse)
async def restore_memory_route(
    record_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordResponse:
    record = await restore_memory(session, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record {record_id} not found or not archived",
        )
    return MemoryRecordResponse.model_validate(record)


@router.get("", response_model=MemoryRecordListResponse)
async def list_memories(
    namespace: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    memory_type: str | None = Query(default=None),
    source: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> MemoryRecordListResponse:
    filters = MemoryRecordFilters(
        namespace=namespace,
        actor_id=actor_id,
        memory_type=memory_type,
        source=source,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    items, total = await list_memory_records(session, filters)
    return MemoryRecordListResponse(
        items=[MemoryRecordResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
