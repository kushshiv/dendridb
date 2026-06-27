from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.association import (
    AssociationCreate,
    AssociationListResponse,
    AssociationResponse,
    AutoLinkRequest,
    AutoLinkResponse,
    RelatedMemoryResponse,
)
from dendridb.core.database import get_db_session
from dendridb.services.association import (
    AssociationFilters,
    auto_link_memories,
    create_association,
    get_association,
    get_related_memories,
    list_associations,
)

router = APIRouter(prefix="/associations", tags=["associations"])


@router.post("", response_model=AssociationResponse, status_code=status.HTTP_201_CREATED)
async def create_association_route(
    payload: AssociationCreate,
    session: AsyncSession = Depends(get_db_session),
) -> AssociationResponse:
    try:
        association = await create_association(session, payload)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Association already exists for this edge",
        ) from exc

    if association is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid association: nodes must exist and differ",
        )
    return AssociationResponse.model_validate(association)


@router.post("/auto-link", response_model=AutoLinkResponse, status_code=status.HTTP_201_CREATED)
async def auto_link_route(
    payload: AutoLinkRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AutoLinkResponse:
    created, skipped = await auto_link_memories(session, payload)
    return AutoLinkResponse(
        created=[AssociationResponse.model_validate(item) for item in created],
        skipped=skipped,
    )


@router.get("/related", response_model=RelatedMemoryResponse)
async def related_memories_route(
    namespace: str = Query(..., min_length=1),
    source_type: str = Query(...),
    source_id: UUID = Query(...),
    depth: int = Query(default=1, ge=1, le=5),
    min_weight: float = Query(default=0.1, ge=0.0, le=1.0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
) -> RelatedMemoryResponse:
    items = await get_related_memories(
        session,
        namespace=namespace,
        source_type=source_type,
        source_id=source_id,
        depth=depth,
        min_weight=min_weight,
        limit=limit,
    )
    if items is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory node {source_type}:{source_id} not found",
        )
    return RelatedMemoryResponse(
        source_type=source_type,
        source_id=source_id,
        items=items,
    )


@router.get("/{association_id}", response_model=AssociationResponse)
async def get_association_route(
    association_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> AssociationResponse:
    association = await get_association(session, association_id)
    if association is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association {association_id} not found",
        )
    return AssociationResponse.model_validate(association)


@router.get("", response_model=AssociationListResponse)
async def list_associations_route(
    namespace: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    source_id: UUID | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: UUID | None = Query(default=None),
    edge_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> AssociationListResponse:
    filters = AssociationFilters(
        namespace=namespace,
        source_type=source_type,
        source_id=source_id,
        target_type=target_type,
        target_id=target_id,
        edge_type=edge_type,
        limit=limit,
        offset=offset,
    )
    associations, total = await list_associations(session, filters)
    return AssociationListResponse(
        items=[AssociationResponse.model_validate(item) for item in associations],
        total=total,
        limit=limit,
        offset=offset,
    )
