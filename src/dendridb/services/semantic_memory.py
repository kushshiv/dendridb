from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.semantic_memory import (
    EvidenceLinkCreate,
    SemanticMemoryCreate,
    SemanticMemoryPromote,
)
from dendridb.memory.promotion import (
    PromotionAction,
    decide_promotion,
    promotion_action_label,
)
from dendridb.models.semantic_memory import SemanticEvidence, SemanticMemory, SemanticMemoryStatus


class SemanticMemoryFilters:
    def __init__(
        self,
        *,
        namespace: str | None = None,
        key: str | None = None,
        actor_id: str | None = None,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        self.namespace = namespace
        self.key = key
        self.actor_id = actor_id
        self.active_only = active_only
        self.limit = limit
        self.offset = offset


def _apply_semantic_filters(query, filters: SemanticMemoryFilters):
    if filters.namespace is not None:
        query = query.where(SemanticMemory.namespace == filters.namespace)
    if filters.key is not None:
        query = query.where(SemanticMemory.key == filters.key)
    if filters.actor_id is not None:
        query = query.where(SemanticMemory.actor_id == filters.actor_id)
    if filters.active_only:
        query = query.where(SemanticMemory.status == SemanticMemoryStatus.ACTIVE.value)
    return query


async def count_semantic_evidence(session: AsyncSession, memory_id: UUID) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(SemanticEvidence)
        .where(SemanticEvidence.semantic_memory_id == memory_id)
    )
    return int(result.scalar_one())


async def get_active_semantic_memory(
    session: AsyncSession,
    *,
    namespace: str,
    key: str,
) -> SemanticMemory | None:
    result = await session.execute(
        select(SemanticMemory).where(
            SemanticMemory.namespace == namespace,
            SemanticMemory.key == key,
            SemanticMemory.status == SemanticMemoryStatus.ACTIVE.value,
        )
    )
    return result.scalar_one_or_none()


async def _existing_evidence_keys(
    session: AsyncSession,
    memory_id: UUID,
) -> set[tuple[str, UUID]]:
    result = await session.execute(
        select(SemanticEvidence.source_type, SemanticEvidence.source_id).where(
            SemanticEvidence.semantic_memory_id == memory_id
        )
    )
    return {(source_type, source_id) for source_type, source_id in result.all()}


async def _attach_evidence(
    session: AsyncSession,
    memory: SemanticMemory,
    evidence: list[EvidenceLinkCreate],
) -> None:
    existing = await _existing_evidence_keys(session, memory.id)
    for link in evidence:
        key = (link.source_type, link.source_id)
        if key in existing:
            continue
        session.add(
            SemanticEvidence(
                semantic_memory_id=memory.id,
                source_type=link.source_type,
                source_id=link.source_id,
            )
        )
        existing.add(key)


async def create_semantic_memory(
    session: AsyncSession,
    payload: SemanticMemoryCreate,
) -> SemanticMemory | None:
    existing = await get_active_semantic_memory(
        session,
        namespace=payload.namespace,
        key=payload.key,
    )
    if existing is not None:
        return None

    memory = SemanticMemory(
        namespace=payload.namespace,
        key=payload.key,
        content=payload.content,
        confidence=payload.confidence,
        version=1,
        status=SemanticMemoryStatus.ACTIVE.value,
        actor_id=payload.actor_id,
        source=payload.source,
        metadata_=payload.metadata,
        provenance=payload.provenance,
    )
    session.add(memory)
    await session.flush()
    await _attach_evidence(session, memory, payload.evidence)
    await session.commit()
    await session.refresh(memory)
    return memory


async def promote_semantic_memory(
    session: AsyncSession,
    payload: SemanticMemoryPromote,
) -> tuple[SemanticMemory, str] | None:
    existing = await get_active_semantic_memory(
        session,
        namespace=payload.namespace,
        key=payload.key,
    )
    decision = decide_promotion(
        has_active=existing is not None,
        existing_content=existing.content if existing else None,
        existing_confidence=existing.confidence if existing else None,
        existing_version=existing.version if existing else None,
        new_content=payload.content,
        new_confidence=payload.confidence,
    )

    if decision.action == PromotionAction.CREATE:
        memory = SemanticMemory(
            namespace=payload.namespace,
            key=payload.key,
            content=payload.content,
            confidence=decision.next_confidence,
            version=decision.next_version,
            status=SemanticMemoryStatus.ACTIVE.value,
            actor_id=payload.actor_id,
            source=payload.source,
            metadata_=payload.metadata,
            provenance=payload.provenance,
        )
        session.add(memory)
        await session.flush()
        await _attach_evidence(session, memory, payload.evidence)
        await session.commit()
        await session.refresh(memory)
        return memory, promotion_action_label(decision.action)

    assert existing is not None

    if decision.action == PromotionAction.MERGE:
        existing.confidence = decision.next_confidence
        if payload.provenance is not None:
            existing.provenance = payload.provenance
        await session.flush()
        await _attach_evidence(session, existing, payload.evidence)
        await session.commit()
        await session.refresh(existing)
        return existing, promotion_action_label(decision.action)

    memory = SemanticMemory(
        namespace=payload.namespace,
        key=payload.key,
        content=payload.content,
        confidence=decision.next_confidence,
        version=decision.next_version,
        status=SemanticMemoryStatus.ACTIVE.value,
        actor_id=payload.actor_id,
        source=payload.source,
        metadata_=payload.metadata,
        provenance=payload.provenance,
    )
    session.add(memory)
    await session.flush()

    existing.status = SemanticMemoryStatus.SUPERSEDED.value
    existing.superseded_by_id = memory.id

    await _attach_evidence(session, memory, payload.evidence)
    await session.commit()
    await session.refresh(memory)
    return memory, promotion_action_label(decision.action)


async def get_semantic_memory(session: AsyncSession, memory_id: UUID) -> SemanticMemory | None:
    return await session.get(SemanticMemory, memory_id)


async def list_semantic_memories(
    session: AsyncSession,
    filters: SemanticMemoryFilters,
) -> tuple[list[SemanticMemory], int]:
    filtered_query = _apply_semantic_filters(select(SemanticMemory), filters)

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = (
        _apply_semantic_filters(select(SemanticMemory), filters)
        .order_by(SemanticMemory.created_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )
    result = await session.execute(list_query)
    return list(result.scalars().all()), total


async def list_semantic_evidence(
    session: AsyncSession,
    memory_id: UUID,
) -> list[SemanticEvidence] | None:
    memory = await session.get(SemanticMemory, memory_id)
    if memory is None:
        return None

    result = await session.execute(
        select(SemanticEvidence)
        .where(SemanticEvidence.semantic_memory_id == memory_id)
        .order_by(SemanticEvidence.created_at.asc())
    )
    return list(result.scalars().all())
