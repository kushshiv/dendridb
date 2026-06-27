from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.association import AssociationCreate, AutoLinkRequest
from dendridb.memory.auto_link import (
    build_content_similarity_candidate,
    build_metadata_match_candidate,
    content_similarity,
    metadata_overlap,
)
from dendridb.memory.traversal import MemoryNodeRef, TraversalEdge, traverse_related_memories
from dendridb.models.association import MemoryAssociation
from dendridb.models.episode import Episode
from dendridb.models.episodic_event import EpisodicEvent
from dendridb.models.memory_record import MemoryRecord
from dendridb.models.semantic_memory import SemanticMemory


@dataclass(frozen=True)
class LinkableMemory:
    node_type: str
    node_id: UUID
    content: str
    metadata: dict[str, Any]


class AssociationFilters:
    def __init__(
        self,
        *,
        namespace: str | None = None,
        source_type: str | None = None,
        source_id: UUID | None = None,
        target_type: str | None = None,
        target_id: UUID | None = None,
        edge_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        self.namespace = namespace
        self.source_type = source_type
        self.source_id = source_id
        self.target_type = target_type
        self.target_id = target_id
        self.edge_type = edge_type
        self.limit = limit
        self.offset = offset


def _apply_association_filters(query, filters: AssociationFilters):
    if filters.namespace is not None:
        query = query.where(MemoryAssociation.namespace == filters.namespace)
    if filters.source_type is not None:
        query = query.where(MemoryAssociation.source_type == filters.source_type)
    if filters.source_id is not None:
        query = query.where(MemoryAssociation.source_id == filters.source_id)
    if filters.target_type is not None:
        query = query.where(MemoryAssociation.target_type == filters.target_type)
    if filters.target_id is not None:
        query = query.where(MemoryAssociation.target_id == filters.target_id)
    if filters.edge_type is not None:
        query = query.where(MemoryAssociation.edge_type == filters.edge_type)
    return query


async def _memory_record_exists(session: AsyncSession, memory_id: UUID) -> bool:
    return await session.get(MemoryRecord, memory_id) is not None


async def _episode_exists(session: AsyncSession, episode_id: UUID) -> bool:
    return await session.get(Episode, episode_id) is not None


async def _episodic_event_exists(session: AsyncSession, event_id: UUID) -> bool:
    return await session.get(EpisodicEvent, event_id) is not None


async def _semantic_memory_exists(session: AsyncSession, memory_id: UUID) -> bool:
    return await session.get(SemanticMemory, memory_id) is not None


async def memory_node_exists(
    session: AsyncSession,
    *,
    node_type: str,
    node_id: UUID,
) -> bool:
    checks = {
        "memory_record": _memory_record_exists,
        "episode": _episode_exists,
        "episodic_event": _episodic_event_exists,
        "semantic_memory": _semantic_memory_exists,
    }
    checker = checks.get(node_type)
    if checker is None:
        return False
    return await checker(session, node_id)


async def create_association(
    session: AsyncSession,
    payload: AssociationCreate,
) -> MemoryAssociation | None:
    if payload.source_id == payload.target_id and payload.source_type == payload.target_type:
        return None

    if not await memory_node_exists(
        session, node_type=payload.source_type, node_id=payload.source_id
    ):
        return None
    if not await memory_node_exists(
        session, node_type=payload.target_type, node_id=payload.target_id
    ):
        return None

    association = MemoryAssociation(
        namespace=payload.namespace,
        source_type=payload.source_type,
        source_id=payload.source_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        edge_type=payload.edge_type,
        weight=payload.weight,
        explanation=payload.explanation,
        metadata_=payload.metadata,
    )
    session.add(association)
    await session.commit()
    await session.refresh(association)
    return association


async def get_association(session: AsyncSession, association_id: UUID) -> MemoryAssociation | None:
    return await session.get(MemoryAssociation, association_id)


async def list_associations(
    session: AsyncSession,
    filters: AssociationFilters,
) -> tuple[list[MemoryAssociation], int]:
    filtered_query = _apply_association_filters(select(MemoryAssociation), filters)
    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = (
        _apply_association_filters(select(MemoryAssociation), filters)
        .order_by(MemoryAssociation.weight.desc(), MemoryAssociation.created_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )
    result = await session.execute(list_query)
    return list(result.scalars().all()), total


async def _load_linkable_memories(
    session: AsyncSession,
    namespace: str,
) -> list[LinkableMemory]:
    items: list[LinkableMemory] = []

    records = await session.execute(select(MemoryRecord).where(MemoryRecord.namespace == namespace))
    for record in records.scalars().all():
        items.append(
            LinkableMemory(
                node_type="memory_record",
                node_id=record.id,
                content=record.content,
                metadata=record.metadata_,
            )
        )

    semantic = await session.execute(
        select(SemanticMemory).where(SemanticMemory.namespace == namespace)
    )
    for memory in semantic.scalars().all():
        items.append(
            LinkableMemory(
                node_type="semantic_memory",
                node_id=memory.id,
                content=memory.content,
                metadata=memory.metadata_,
            )
        )

    episodes = await session.execute(select(Episode).where(Episode.namespace == namespace))
    for episode in episodes.scalars().all():
        content = episode.summary or episode.title or ""
        items.append(
            LinkableMemory(
                node_type="episode",
                node_id=episode.id,
                content=content,
                metadata=episode.metadata_,
            )
        )

    events = await session.execute(
        select(EpisodicEvent)
        .join(Episode, EpisodicEvent.episode_id == Episode.id)
        .where(Episode.namespace == namespace)
    )
    for event in events.scalars().all():
        items.append(
            LinkableMemory(
                node_type="episodic_event",
                node_id=event.id,
                content=event.content,
                metadata=event.metadata_,
            )
        )

    return items


async def _association_exists(
    session: AsyncSession,
    *,
    namespace: str,
    source_type: str,
    source_id: UUID,
    target_type: str,
    target_id: UUID,
    edge_type: str,
) -> bool:
    result = await session.execute(
        select(MemoryAssociation.id).where(
            MemoryAssociation.namespace == namespace,
            MemoryAssociation.source_type == source_type,
            MemoryAssociation.source_id == source_id,
            MemoryAssociation.target_type == target_type,
            MemoryAssociation.target_id == target_id,
            MemoryAssociation.edge_type == edge_type,
        )
    )
    return result.scalar_one_or_none() is not None


async def auto_link_memories(
    session: AsyncSession,
    payload: AutoLinkRequest,
) -> tuple[list[MemoryAssociation], int]:
    memories = await _load_linkable_memories(session, payload.namespace)
    if payload.source_type is not None and payload.source_id is not None:
        sources = [
            memory
            for memory in memories
            if memory.node_type == payload.source_type and memory.node_id == payload.source_id
        ]
    else:
        sources = memories

    created: list[MemoryAssociation] = []
    skipped = 0

    for source in sources:
        candidates: list[tuple[LinkableMemory, str, float, str]] = []
        for target in memories:
            if source.node_type == target.node_type and source.node_id == target.node_id:
                continue

            if payload.metadata_match:
                score, shared_paths = metadata_overlap(source.metadata, target.metadata)
                candidate = build_metadata_match_candidate(
                    target_type=target.node_type,
                    target_id=str(target.node_id),
                    overlap_score=score,
                    shared_paths=shared_paths,
                )
                if candidate is not None:
                    candidates.append(
                        (target, candidate.edge_type, candidate.weight, candidate.explanation)
                    )

            if payload.content_similarity and source.content and target.content:
                similarity = content_similarity(source.content, target.content)
                candidate = build_content_similarity_candidate(
                    target_type=target.node_type,
                    target_id=str(target.node_id),
                    similarity=similarity,
                    threshold=payload.similarity_threshold,
                )
                if candidate is not None:
                    candidates.append(
                        (target, candidate.edge_type, candidate.weight, candidate.explanation)
                    )

        candidates.sort(key=lambda item: item[2], reverse=True)
        selected = candidates[: payload.limit]

        for target, edge_type, weight, explanation in selected:
            if await _association_exists(
                session,
                namespace=payload.namespace,
                source_type=source.node_type,
                source_id=source.node_id,
                target_type=target.node_type,
                target_id=target.node_id,
                edge_type=edge_type,
            ):
                skipped += 1
                continue

            association = MemoryAssociation(
                namespace=payload.namespace,
                source_type=source.node_type,
                source_id=source.node_id,
                target_type=target.node_type,
                target_id=target.node_id,
                edge_type=edge_type,
                weight=weight,
                explanation=explanation,
            )
            session.add(association)
            created.append(association)

    if created:
        await session.commit()
        for association in created:
            await session.refresh(association)

    return created, skipped


async def _load_edges_for_namespace(
    session: AsyncSession,
    namespace: str,
) -> list[MemoryAssociation]:
    result = await session.execute(
        select(MemoryAssociation).where(MemoryAssociation.namespace == namespace)
    )
    return list(result.scalars().all())


async def get_related_memories(
    session: AsyncSession,
    *,
    namespace: str,
    source_type: str,
    source_id: UUID,
    depth: int,
    min_weight: float,
    limit: int,
) -> list[dict[str, Any]] | None:
    if not await memory_node_exists(session, node_type=source_type, node_id=source_id):
        return None

    associations = await _load_edges_for_namespace(session, namespace)
    edges = [
        TraversalEdge(
            association_id=association.id,
            edge_type=association.edge_type,
            weight=association.weight,
            explanation=association.explanation,
            direction="outbound",
            from_node=MemoryNodeRef(
                node_type=association.source_type,
                node_id=association.source_id,
            ),
            to_node=MemoryNodeRef(
                node_type=association.target_type,
                node_id=association.target_id,
            ),
        )
        for association in associations
    ]

    start = MemoryNodeRef(node_type=source_type, node_id=source_id)
    related = traverse_related_memories(
        start=start,
        edges=edges,
        max_depth=depth,
        min_weight=min_weight,
    )[:limit]

    items: list[dict[str, Any]] = []
    for result in related:
        summary = await _build_node_summary(
            session,
            node_type=result.node.node_type,
            node_id=result.node.node_id,
        )
        items.append(
            {
                "node_type": result.node.node_type,
                "node_id": result.node.node_id,
                "depth": result.depth,
                "path_weight": result.path_weight,
                "explanation": result.explanation,
                "summary": summary,
            }
        )
    return items


async def _build_node_summary(
    session: AsyncSession,
    *,
    node_type: str,
    node_id: UUID,
) -> dict[str, Any]:
    if node_type == "memory_record":
        record = await session.get(MemoryRecord, node_id)
        if record is None:
            return {}
        return {
            "content": record.content,
            "memory_type": record.memory_type,
            "metadata": record.metadata_,
        }
    if node_type == "semantic_memory":
        memory = await session.get(SemanticMemory, node_id)
        if memory is None:
            return {}
        return {
            "key": memory.key,
            "content": memory.content,
            "confidence": memory.confidence,
            "status": memory.status,
        }
    if node_type == "episode":
        episode = await session.get(Episode, node_id)
        if episode is None:
            return {}
        return {
            "session_id": episode.session_id,
            "title": episode.title,
            "summary": episode.summary,
        }
    if node_type == "episodic_event":
        event = await session.get(EpisodicEvent, node_id)
        if event is None:
            return {}
        return {
            "content": event.content,
            "event_type": event.event_type,
            "sequence_number": event.sequence_number,
        }
    return {}
