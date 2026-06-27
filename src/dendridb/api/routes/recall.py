from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.recall import (
    RecallExplanation,
    RecallRequest,
    RecallResponse,
    RecallWeights,
    ReindexRequest,
    ReindexResponse,
    build_recall_memory_result,
)
from dendridb.core.database import get_db_session
from dendridb.services.recall import recall_memories, reindex_namespace_embeddings

router = APIRouter(prefix="/recall", tags=["recall"])


@router.post("", response_model=RecallResponse)
async def recall_route(
    payload: RecallRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RecallResponse:
    scored, total_candidates = await recall_memories(session, payload)
    items = []
    for result in scored:
        items.append(
            build_recall_memory_result(
                result.record,
                score=result.hybrid_score,
                explanation=RecallExplanation(
                    summary=result.summary,
                    factors=result.factors,
                    contributions=result.contributions,
                    weights=RecallWeights(
                        similarity=payload.weights.similarity,
                        recency=payload.weights.recency,
                        salience=payload.weights.salience,
                        association=payload.weights.association,
                    ),
                ),
            )
        )
    return RecallResponse(
        query=payload.query,
        namespace=payload.namespace,
        items=items,
        total_candidates=total_candidates,
    )


@router.post("/reindex", response_model=ReindexResponse, status_code=status.HTTP_200_OK)
async def reindex_route(
    payload: ReindexRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ReindexResponse:
    updated = await reindex_namespace_embeddings(
        session,
        namespace=payload.namespace,
        limit=payload.limit,
    )
    return ReindexResponse(namespace=payload.namespace, updated=updated)
