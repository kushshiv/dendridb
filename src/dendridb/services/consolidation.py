from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.consolidation import ConsolidationRunRequest, ConsolidationStats
from dendridb.api.schemas.semantic_memory import EvidenceLinkCreate, SemanticMemoryPromote
from dendridb.memory.consolidation import (
    find_duplicate_pairs,
    find_repeated_patterns,
    is_merged_record,
)
from dendridb.memory.summarize import Summarizer, default_summarizer
from dendridb.models.consolidation_job import ConsolidationJobRun, ConsolidationJobStatus
from dendridb.models.episode import Episode
from dendridb.models.memory_record import MemoryRecord
from dendridb.services.episode import replay_episode
from dendridb.services.job_dispatch import (
    celery_runs_inline,
    dispatch_consolidation,
    uses_celery_queue,
)
from dendridb.services.semantic_memory import promote_semantic_memory


@dataclass(frozen=True)
class ConsolidationOptions:
    lookback_hours: int = 168
    duplicate_similarity_threshold: float = 0.85
    min_pattern_occurrences: int = 2
    dry_run: bool = False


async def create_consolidation_job(
    session: AsyncSession,
    *,
    namespace: str,
    trigger: str,
    dry_run: bool,
) -> ConsolidationJobRun:
    job = ConsolidationJobRun(
        namespace=namespace,
        status=ConsolidationJobStatus.PENDING.value,
        trigger=trigger,
        dry_run=dry_run,
        stats={},
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_consolidation_job(session: AsyncSession, job_id: UUID) -> ConsolidationJobRun | None:
    return await session.get(ConsolidationJobRun, job_id)


async def list_consolidation_jobs(
    session: AsyncSession,
    *,
    namespace: str | None,
    limit: int,
    offset: int,
) -> tuple[list[ConsolidationJobRun], int]:
    query = select(ConsolidationJobRun)
    if namespace is not None:
        query = query.where(ConsolidationJobRun.namespace == namespace)

    count_query = select(func.count()).select_from(query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = query.order_by(ConsolidationJobRun.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(list_query)
    return list(result.scalars().all()), total


async def _load_recent_episodes(
    session: AsyncSession,
    *,
    namespace: str,
    lookback_hours: int,
) -> list[Episode]:
    cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
    result = await session.execute(
        select(Episode)
        .where(Episode.namespace == namespace, Episode.created_at >= cutoff)
        .order_by(Episode.created_at.desc())
    )
    return list(result.scalars().all())


async def _load_memory_records(session: AsyncSession, *, namespace: str) -> list[MemoryRecord]:
    result = await session.execute(
        select(MemoryRecord)
        .where(MemoryRecord.namespace == namespace)
        .order_by(MemoryRecord.created_at.desc())
    )
    return list(result.scalars().all())


async def run_consolidation_job(
    session: AsyncSession,
    job: ConsolidationJobRun,
    options: ConsolidationOptions,
    *,
    summarizer: Summarizer | None = None,
) -> ConsolidationJobRun:
    summarize = summarizer or default_summarizer
    job.status = ConsolidationJobStatus.RUNNING.value
    await session.commit()

    stats = ConsolidationStats()
    try:
        episodes = await _load_recent_episodes(
            session,
            namespace=job.namespace,
            lookback_hours=options.lookback_hours,
        )
        replay_events: list[tuple[UUID, UUID, str]] = []
        for episode in episodes:
            replay = await replay_episode(session, episode.id)
            if replay is None:
                continue
            _, events = replay
            stats.episodes_replayed += 1
            stats.events_replayed += len(events)
            for event in events:
                replay_events.append((episode.id, event.id, event.content))

        patterns = find_repeated_patterns(
            replay_events,
            min_occurrences=options.min_pattern_occurrences,
        )
        for pattern in patterns:
            summary = summarize([pattern.content])
            promote_payload = SemanticMemoryPromote(
                namespace=job.namespace,
                key=pattern.key,
                content=summary,
                confidence=pattern.confidence,
                source="consolidation",
                provenance={"consolidation_job_id": str(job.id)},
                evidence=[
                    EvidenceLinkCreate(source_type="episodic_event", source_id=event_id)
                    for event_id in pattern.event_ids
                ],
            )
            if options.dry_run:
                stats.patterns_promoted += 1
                stats.promotion_actions.append("created")
                continue

            result = await promote_semantic_memory(session, promote_payload)
            if result is None:
                continue
            _, action = result
            stats.patterns_promoted += 1
            stats.promotion_actions.append(action)
            if action == "merged":
                stats.patterns_merged += 1

        records = await _load_memory_records(session, namespace=job.namespace)
        duplicate_input = [
            (
                record.id,
                record.content,
                record.salience,
                record.created_at,
                record.metadata_,
            )
            for record in records
        ]
        duplicate_pairs = find_duplicate_pairs(
            duplicate_input,
            similarity_threshold=options.duplicate_similarity_threshold,
        )
        for pair in duplicate_pairs:
            stats.duplicate_pairs.append(
                {
                    "keep_id": str(pair.keep_id),
                    "merge_id": str(pair.merge_id),
                    "similarity": pair.similarity,
                }
            )
            if options.dry_run:
                stats.duplicates_merged += 1
                continue

            keep = await session.get(MemoryRecord, pair.keep_id)
            merge = await session.get(MemoryRecord, pair.merge_id)
            if keep is None or merge is None or is_merged_record(merge.metadata_):
                continue

            merge.metadata_ = {
                **merge.metadata_,
                "consolidation_status": "merged",
                "merged_into": str(keep.id),
                "consolidation_job_id": str(job.id),
            }
            if keep.salience is not None:
                keep.salience = min(10.0, keep.salience + 0.1)
            stats.duplicates_merged += 1

        if not options.dry_run:
            await session.commit()

        job.status = ConsolidationJobStatus.COMPLETED.value
        job.stats = stats.model_dump()
        job.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(job)
        return job
    except Exception as exc:
        job.status = ConsolidationJobStatus.FAILED.value
        job.error_message = str(exc)
        job.stats = stats.model_dump()
        job.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(job)
        raise


async def start_consolidation(
    session: AsyncSession,
    payload: ConsolidationRunRequest,
    *,
    trigger: str = "manual",
    summarizer: Summarizer | None = None,
) -> ConsolidationJobRun:
    job = await create_consolidation_job(
        session,
        namespace=payload.namespace,
        trigger=trigger,
        dry_run=payload.dry_run,
    )
    options = ConsolidationOptions(
        lookback_hours=payload.lookback_hours,
        duplicate_similarity_threshold=payload.duplicate_similarity_threshold,
        min_pattern_occurrences=payload.min_pattern_occurrences,
        dry_run=payload.dry_run,
    )
    if uses_celery_queue():
        job_id = job.id
        await dispatch_consolidation(
            session,
            job_id,
            {
                "lookback_hours": options.lookback_hours,
                "duplicate_similarity_threshold": options.duplicate_similarity_threshold,
                "min_pattern_occurrences": options.min_pattern_occurrences,
                "dry_run": options.dry_run,
            },
        )
        if celery_runs_inline():
            session.expire_all()
            refreshed = await get_consolidation_job(session, job_id)
            return refreshed or job
        return job
    return await run_consolidation_job(session, job, options, summarizer=summarizer)
