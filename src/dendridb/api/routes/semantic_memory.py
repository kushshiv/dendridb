from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.semantic_memory import (
    EvidenceLinkResponse,
    SemanticMemoryCreate,
    SemanticMemoryEvidenceResponse,
    SemanticMemoryListResponse,
    SemanticMemoryPromote,
    SemanticMemoryPromoteResponse,
    SemanticMemoryResponse,
    build_semantic_memory_response,
)
from dendridb.core.database import get_db_session
from dendridb.services.semantic_memory import (
    SemanticMemoryFilters,
    count_semantic_evidence,
    create_semantic_memory,
    get_semantic_memory,
    list_semantic_evidence,
    list_semantic_memories,
    promote_semantic_memory,
)

router = APIRouter(prefix="/semantic-memory", tags=["semantic-memory"])


@router.post("", response_model=SemanticMemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_semantic_memory_route(
    payload: SemanticMemoryCreate,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticMemoryResponse:
    memory = await create_semantic_memory(session, payload)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Active semantic memory already exists for key '{payload.key}'",
        )
    count = await count_semantic_evidence(session, memory.id)
    return build_semantic_memory_response(memory, evidence_count=count)


@router.post(
    "/promote",
    response_model=SemanticMemoryPromoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_semantic_memory_route(
    payload: SemanticMemoryPromote,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticMemoryPromoteResponse:
    result = await promote_semantic_memory(session, payload)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Promotion failed",
        )
    memory, action = result
    count = await count_semantic_evidence(session, memory.id)
    return SemanticMemoryPromoteResponse(
        memory=build_semantic_memory_response(memory, evidence_count=count),
        action=action,
    )


@router.get("/{memory_id}", response_model=SemanticMemoryResponse)
async def get_semantic_memory_route(
    memory_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticMemoryResponse:
    memory = await get_semantic_memory(session, memory_id)
    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semantic memory {memory_id} not found",
        )
    count = await count_semantic_evidence(session, memory_id)
    return build_semantic_memory_response(memory, evidence_count=count)


@router.get("/{memory_id}/evidence", response_model=SemanticMemoryEvidenceResponse)
async def list_semantic_evidence_route(
    memory_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> SemanticMemoryEvidenceResponse:
    evidence = await list_semantic_evidence(session, memory_id)
    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Semantic memory {memory_id} not found",
        )
    return SemanticMemoryEvidenceResponse(
        items=[EvidenceLinkResponse.model_validate(item) for item in evidence]
    )


@router.get("", response_model=SemanticMemoryListResponse)
async def list_semantic_memories_route(
    namespace: str | None = Query(default=None),
    key: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> SemanticMemoryListResponse:
    filters = SemanticMemoryFilters(
        namespace=namespace,
        key=key,
        actor_id=actor_id,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    memories, total = await list_semantic_memories(session, filters)
    items = []
    for memory in memories:
        count = await count_semantic_evidence(session, memory.id)
        items.append(build_semantic_memory_response(memory, evidence_count=count))
    return SemanticMemoryListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
