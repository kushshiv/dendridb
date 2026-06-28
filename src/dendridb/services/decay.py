from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.decay import DecayRunRequest, DecayStats
from dendridb.config import get_settings
from dendridb.memory.consolidation import is_merged_record
from dendridb.memory.decay_policy import (
    DecayPolicy,
    age_hours_since,
    compute_decayed_salience,
    reinforce_salience,
    should_archive,
)
from dendridb.memory.visibility import is_archived_record
from dendridb.models.decay_job import DecayJobRun, DecayJobStatus
from dendridb.models.memory_record import MemoryRecord
from dendridb.services.job_dispatch import celery_runs_inline, dispatch_decay, uses_celery_queue


def policy_from_settings(overrides: DecayRunRequest | None = None) -> DecayPolicy:
    settings = get_settings()
    return DecayPolicy(
        half_life_hours=(
            overrides.half_life_hours
            if overrides and overrides.half_life_hours is not None
            else settings.decay_half_life_hours
        ),
        min_salience=(
            overrides.min_salience
            if overrides and overrides.min_salience is not None
            else settings.decay_min_salience
        ),
        max_salience=settings.decay_max_salience,
        retrieval_strengthen_delta=settings.retrieval_strengthen_delta,
    )


async def create_decay_job(
    session: AsyncSession,
    *,
    namespace: str,
    trigger: str,
    dry_run: bool,
) -> DecayJobRun:
    job = DecayJobRun(
        namespace=namespace,
        status=DecayJobStatus.PENDING.value,
        trigger=trigger,
        dry_run=dry_run,
        stats={},
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def get_decay_job(session: AsyncSession, job_id: UUID) -> DecayJobRun | None:
    return await session.get(DecayJobRun, job_id)


async def list_decay_jobs(
    session: AsyncSession,
    *,
    namespace: str | None,
    limit: int,
    offset: int,
) -> tuple[list[DecayJobRun], int]:
    query = select(DecayJobRun)
    if namespace is not None:
        query = query.where(DecayJobRun.namespace == namespace)

    count_query = select(func.count()).select_from(query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = query.order_by(DecayJobRun.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(list_query)
    return list(result.scalars().all()), total


async def run_decay_job(
    session: AsyncSession,
    job: DecayJobRun,
    policy: DecayPolicy,
) -> DecayJobRun:
    job.status = DecayJobStatus.RUNNING.value
    await session.commit()

    stats = DecayStats()
    now = datetime.now(UTC)
    try:
        result = await session.execute(
            select(MemoryRecord).where(MemoryRecord.namespace == job.namespace)
        )
        records = list(result.scalars().all())

        for record in records:
            stats.records_scanned += 1
            if is_merged_record(record.metadata_) or is_archived_record(record.archived_at):
                continue
            if record.pinned:
                stats.records_skipped_pinned += 1
                continue

            reference = record.last_retrieved_at or record.updated_at or record.created_at
            age = age_hours_since(reference, now=now)
            new_salience = compute_decayed_salience(
                record.salience,
                age_hours=age,
                policy=policy,
                pinned=record.pinned,
            )

            if should_archive(new_salience, policy=policy, pinned=record.pinned):
                stats.records_archived += 1
                if not job.dry_run:
                    record.archived_at = now
                    record.salience = new_salience
                continue

            if new_salience != (record.salience if record.salience is not None else 0.5):
                stats.records_decayed += 1
                if not job.dry_run:
                    record.salience = new_salience

        if not job.dry_run:
            await session.commit()

        job.status = DecayJobStatus.COMPLETED.value
        job.stats = stats.model_dump()
        job.completed_at = now
        await session.commit()
        await session.refresh(job)
        return job
    except Exception as exc:
        job.status = DecayJobStatus.FAILED.value
        job.error_message = str(exc)
        job.stats = stats.model_dump()
        job.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(job)
        raise


async def start_decay(
    session: AsyncSession,
    payload: DecayRunRequest,
    *,
    trigger: str = "manual",
) -> DecayJobRun:
    job = await create_decay_job(
        session,
        namespace=payload.namespace,
        trigger=trigger,
        dry_run=payload.dry_run,
    )
    if uses_celery_queue():
        job_id = job.id
        await dispatch_decay(session, job_id, payload.model_dump())
        if celery_runs_inline():
            session.expire_all()
            refreshed = await get_decay_job(session, job_id)
            return refreshed or job
        return job
    policy = policy_from_settings(payload)
    return await run_decay_job(session, job, policy)


async def pin_memory(session: AsyncSession, record_id: UUID) -> MemoryRecord | None:
    record = await session.get(MemoryRecord, record_id)
    if record is None or is_archived_record(record.archived_at):
        return None
    record.pinned = True
    await session.commit()
    await session.refresh(record)
    return record


async def unpin_memory(session: AsyncSession, record_id: UUID) -> MemoryRecord | None:
    record = await session.get(MemoryRecord, record_id)
    if record is None:
        return None
    record.pinned = False
    await session.commit()
    await session.refresh(record)
    return record


async def archive_memory(session: AsyncSession, record_id: UUID) -> MemoryRecord | None:
    record = await session.get(MemoryRecord, record_id)
    if record is None or is_archived_record(record.archived_at):
        return None
    record.archived_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(record)
    return record


async def restore_memory(session: AsyncSession, record_id: UUID) -> MemoryRecord | None:
    record = await session.get(MemoryRecord, record_id)
    if record is None or not is_archived_record(record.archived_at):
        return None
    record.archived_at = None
    await session.commit()
    await session.refresh(record)
    return record


async def reinforce_memories(session: AsyncSession, records: list[MemoryRecord]) -> None:
    if not records:
        return
    policy = policy_from_settings()
    now = datetime.now(UTC)
    for record in records:
        record.salience = reinforce_salience(record.salience, policy=policy)
        record.last_retrieved_at = now
    await session.commit()
    for record in records:
        await session.refresh(record)
