from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.recall import RecallRequest
from dendridb.config import get_settings
from dendridb.memory.consolidation import is_merged_record
from dendridb.memory.embeddings import embed_text
from dendridb.models.association import MemoryAssociation
from dendridb.models.memory_record import MemoryRecord
from dendridb.ranking.hybrid import (
    build_recall_summary,
    compute_hybrid_score,
    recency_score,
    salience_score,
)


@dataclass(frozen=True)
class ScoredMemory:
    record: MemoryRecord
    similarity: float
    association: float
    hybrid_score: float
    factors: dict[str, float]
    contributions: dict[str, float]
    summary: str


async def set_memory_embedding(session: AsyncSession, record: MemoryRecord) -> None:
    settings = get_settings()
    record.embedding = embed_text(record.content, dimensions=settings.embedding_dimensions)
    session.add(record)


async def reindex_namespace_embeddings(
    session: AsyncSession,
    *,
    namespace: str,
    limit: int,
) -> int:
    result = await session.execute(
        select(MemoryRecord)
        .where(MemoryRecord.namespace == namespace)
        .order_by(MemoryRecord.created_at.desc())
        .limit(limit)
    )
    records = list(result.scalars().all())
    updated = 0
    for record in records:
        await set_memory_embedding(session, record)
        updated += 1
    if updated:
        await session.commit()
    return updated


async def _association_scores(
    session: AsyncSession,
    *,
    namespace: str,
    context_memory_id: UUID,
    candidate_ids: list[UUID],
) -> dict[UUID, float]:
    if not candidate_ids:
        return {}

    result = await session.execute(
        select(MemoryAssociation).where(
            MemoryAssociation.namespace == namespace,
            or_(
                MemoryAssociation.source_type == "memory_record",
                MemoryAssociation.target_type == "memory_record",
            ),
            or_(
                MemoryAssociation.source_id == context_memory_id,
                MemoryAssociation.target_id == context_memory_id,
            ),
        )
    )
    associations = list(result.scalars().all())
    scores: dict[UUID, float] = {}
    for association in associations:
        if (
            association.source_type == "memory_record"
            and association.source_id == context_memory_id
            and association.target_type == "memory_record"
            and association.target_id in candidate_ids
        ):
            target_id = association.target_id
        elif (
            association.target_type == "memory_record"
            and association.target_id == context_memory_id
            and association.source_type == "memory_record"
            and association.source_id in candidate_ids
        ):
            target_id = association.source_id
        else:
            continue

        scores[target_id] = max(scores.get(target_id, 0.0), association.weight)
    return scores


async def recall_memories(
    session: AsyncSession,
    payload: RecallRequest,
) -> tuple[list[ScoredMemory], int]:
    settings = get_settings()
    query_embedding = embed_text(payload.query, dimensions=settings.embedding_dimensions)
    now = datetime.now(UTC)

    similarity_expr = 1 - MemoryRecord.embedding.cosine_distance(query_embedding)
    candidate_query = (
        select(MemoryRecord, similarity_expr.label("similarity"))
        .where(
            MemoryRecord.namespace == payload.namespace,
            MemoryRecord.embedding.isnot(None),
        )
        .order_by(MemoryRecord.embedding.cosine_distance(query_embedding))
        .limit(payload.candidate_limit)
    )
    result = await session.execute(candidate_query)
    rows = result.all()
    total_candidates = len(rows)

    candidate_ids = [row[0].id for row in rows]
    association_map: dict[UUID, float] = {}
    if payload.context_memory_id is not None:
        association_map = await _association_scores(
            session,
            namespace=payload.namespace,
            context_memory_id=payload.context_memory_id,
            candidate_ids=candidate_ids,
        )

    weights = payload.weights.to_ranking_weights()
    scored: list[ScoredMemory] = []
    for record, similarity in rows:
        if is_merged_record(record.metadata_):
            continue
        hybrid = compute_hybrid_score(
            similarity=float(similarity),
            recency=recency_score(record.created_at, now=now),
            salience=salience_score(record.salience),
            association=association_map.get(record.id, 0.0),
            weights=weights,
        )
        if hybrid.score < payload.min_score:
            continue
        scored.append(
            ScoredMemory(
                record=record,
                similarity=float(similarity),
                association=association_map.get(record.id, 0.0),
                hybrid_score=hybrid.score,
                factors=hybrid.factors.as_dict(),
                contributions=hybrid.contributions,
                summary=build_recall_summary(hybrid.contributions),
            )
        )

    scored.sort(key=lambda item: (-item.hybrid_score, -item.similarity))
    return scored[: payload.limit], total_candidates
