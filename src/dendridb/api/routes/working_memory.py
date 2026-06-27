from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.working_memory import (
    WorkingMemoryCreate,
    WorkingMemoryListResponse,
    WorkingMemoryReplace,
    WorkingMemoryResponse,
    WorkingMemoryUpdate,
)
from dendridb.core.database import get_db_session
from dendridb.services.working_memory import (
    WorkingMemoryFilters,
    create_working_memory_item,
    get_working_memory_item,
    list_working_memory_items,
    replace_working_memory_item,
    update_working_memory_item,
)

router = APIRouter(prefix="/working-memory", tags=["working-memory"])


@router.post("", response_model=WorkingMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_working_memory(
    payload: WorkingMemoryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkingMemoryResponse:
    try:
        item = await create_working_memory_item(session, payload)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Working memory key already exists for this session. "
                "Use PUT /working-memory/replace instead."
            ),
        ) from exc
    return WorkingMemoryResponse.model_validate(item)


@router.put("/replace", response_model=WorkingMemoryResponse)
async def replace_working_memory(
    payload: WorkingMemoryReplace,
    session: AsyncSession = Depends(get_db_session),
) -> WorkingMemoryResponse:
    item = await replace_working_memory_item(session, payload)
    return WorkingMemoryResponse.model_validate(item)


@router.get("/{item_id}", response_model=WorkingMemoryResponse)
async def get_working_memory(
    item_id: UUID,
    include_expired: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
) -> WorkingMemoryResponse:
    item = await get_working_memory_item(
        session,
        item_id,
        include_expired=include_expired,
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Working memory item {item_id} not found",
        )
    return WorkingMemoryResponse.model_validate(item)


@router.patch("/{item_id}", response_model=WorkingMemoryResponse)
async def update_working_memory(
    item_id: UUID,
    payload: WorkingMemoryUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> WorkingMemoryResponse:
    item = await update_working_memory_item(session, item_id, payload)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Working memory item {item_id} not found",
        )
    return WorkingMemoryResponse.model_validate(item)


@router.get("", response_model=WorkingMemoryListResponse)
async def list_working_memory(
    namespace: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    include_expired: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> WorkingMemoryListResponse:
    filters = WorkingMemoryFilters(
        namespace=namespace,
        session_id=session_id,
        task_id=task_id,
        include_expired=include_expired,
        limit=limit,
        offset=offset,
    )
    items, total = await list_working_memory_items(session, filters)
    return WorkingMemoryListResponse(
        items=[WorkingMemoryResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
