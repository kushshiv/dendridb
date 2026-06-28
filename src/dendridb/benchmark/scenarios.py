"""Individual benchmark scenarios."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.consolidation import ConsolidationRunRequest
from dendridb.api.schemas.episode import EpisodeCreate, EpisodicEventCreate
from dendridb.api.schemas.memory_record import MemoryRecordCreate
from dendridb.api.schemas.recall import RecallRequest
from dendridb.benchmark.dataset import BenchmarkDataset
from dendridb.benchmark.timing import measure_async, summarize_seconds, to_milliseconds
from dendridb.models.consolidation_job import ConsolidationJobRun
from dendridb.models.decay_job import DecayJobRun
from dendridb.models.episode import Episode
from dendridb.models.episodic_event import EpisodicEvent
from dendridb.models.memory_record import MemoryRecord
from dendridb.models.semantic_memory import SemanticMemory
from dendridb.services.consolidation import start_consolidation
from dendridb.services.episode import append_episodic_event, create_episode
from dendridb.services.memory_record import create_memory_record
from dendridb.services.recall import recall_memories


async def cleanup_namespace(session: AsyncSession, namespace: str) -> None:
    from sqlalchemy import delete

    from dendridb.models.association import MemoryAssociation

    await session.execute(
        delete(EpisodicEvent).where(
            EpisodicEvent.episode_id.in_(select(Episode.id).where(Episode.namespace == namespace))
        )
    )
    await session.execute(delete(Episode).where(Episode.namespace == namespace))
    await session.execute(delete(MemoryAssociation).where(MemoryAssociation.namespace == namespace))
    await session.execute(delete(SemanticMemory).where(SemanticMemory.namespace == namespace))
    await session.execute(delete(MemoryRecord).where(MemoryRecord.namespace == namespace))
    await session.execute(
        delete(ConsolidationJobRun).where(ConsolidationJobRun.namespace == namespace)
    )
    await session.execute(delete(DecayJobRun).where(DecayJobRun.namespace == namespace))
    await session.commit()


async def seed_consolidation_episodes(
    session: AsyncSession,
    *,
    namespace: str,
    dataset: BenchmarkDataset,
) -> None:
    if dataset.consolidation is None:
        return
    for episode_fixture in dataset.consolidation.episodes:
        episode = await create_episode(
            session,
            EpisodeCreate(namespace=namespace, session_id=episode_fixture.session_id),
        )
        for content in episode_fixture.events:
            await append_episodic_event(
                session,
                episode.id,
                EpisodicEventCreate(content=content),
            )


async def run_ingestion_benchmark(
    session: AsyncSession,
    *,
    namespace: str,
    dataset: BenchmarkDataset,
) -> dict:
    latencies: list[float] = []
    created = 0

    for memory in dataset.memories:
        _, elapsed = await measure_async(
            lambda memory=memory: create_memory_record(
                session,
                MemoryRecordCreate(
                    namespace=namespace,
                    content=memory.content,
                    salience=memory.salience,
                    metadata=memory.metadata,
                    source=memory.source,
                ),
            )
        )
        latencies.append(elapsed)
        created += 1

    summary = summarize_seconds(latencies)
    total_seconds = summary["total_seconds"]
    throughput = created / total_seconds if total_seconds > 0 else 0.0
    return {
        "records_created": created,
        "throughput_records_per_second": round(throughput, 3),
        "latency_ms": {key: to_milliseconds(value) for key, value in summary.items()},
    }


async def run_recall_benchmark(
    session: AsyncSession,
    *,
    namespace: str,
    dataset: BenchmarkDataset,
) -> dict:
    latencies: list[float] = []
    hits = 0
    queries = 0
    candidate_totals: list[int] = []

    for query_fixture in dataset.recall_queries:
        queries += 1
        request = RecallRequest(
            namespace=namespace,
            query=query_fixture.query,
            limit=query_fixture.limit,
        )

        async def _recall(request=request):
            return await recall_memories(session, request)

        (scored, total_candidates), elapsed = await measure_async(_recall)
        latencies.append(elapsed)
        candidate_totals.append(total_candidates)

        if not query_fixture.expected_in_top_k:
            continue

        top_contents = [item.record.content.lower() for item in scored]
        matched = all(
            any(expected.lower() in content for content in top_contents)
            for expected in query_fixture.expected_in_top_k
        )
        if matched:
            hits += 1

    quality_queries = sum(1 for item in dataset.recall_queries if item.expected_in_top_k)
    hit_rate = hits / quality_queries if quality_queries else 1.0
    summary = summarize_seconds(latencies)
    candidate_mean = sum(candidate_totals) / len(candidate_totals) if candidate_totals else 0.0
    return {
        "queries_run": queries,
        "quality_queries": quality_queries,
        "quality_hits": hits,
        "quality_hit_rate": round(hit_rate, 3),
        "total_candidates_mean": round(candidate_mean, 3),
        "latency_ms": {key: to_milliseconds(value) for key, value in summary.items()},
    }


async def run_consolidation_benchmark(
    session: AsyncSession,
    *,
    namespace: str,
    dataset: BenchmarkDataset,
) -> dict:
    if dataset.consolidation is None or not dataset.consolidation.episodes:
        return {
            "skipped": True,
            "reason": "no consolidation fixtures in dataset",
        }

    min_occurrences = dataset.consolidation.min_pattern_occurrences
    job, elapsed = await measure_async(
        lambda: start_consolidation(
            session,
            ConsolidationRunRequest(
                namespace=namespace,
                min_pattern_occurrences=min_occurrences,
            ),
            trigger="benchmark",
        )
    )
    stats = job.stats or {}
    return {
        "skipped": False,
        "job_status": job.status,
        "duration_ms": to_milliseconds(elapsed),
        "stats": stats,
    }


async def run_storage_snapshot(session: AsyncSession, *, namespace: str) -> dict:
    async def _count(model, *, extra_filter=None) -> int:
        query = select(func.count()).select_from(model).where(model.namespace == namespace)
        if extra_filter is not None:
            query = extra_filter(query)
        return int((await session.execute(query)).scalar_one())

    memory_records = await _count(MemoryRecord)
    active_memories = await _count(
        MemoryRecord,
        extra_filter=lambda query: query.where(MemoryRecord.archived_at.is_(None)),
    )
    episodes = await _count(Episode)
    semantic_memories = await _count(SemanticMemory)
    events = int(
        (
            await session.execute(
                select(func.count())
                .select_from(EpisodicEvent)
                .where(
                    EpisodicEvent.episode_id.in_(
                        select(Episode.id).where(Episode.namespace == namespace)
                    )
                )
            )
        ).scalar_one()
    )

    return {
        "memory_records": memory_records,
        "active_memory_records": active_memories,
        "episodes": episodes,
        "episodic_events": events,
        "semantic_memories": semantic_memories,
    }
