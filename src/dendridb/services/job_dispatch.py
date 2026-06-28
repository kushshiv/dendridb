from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.config import get_settings


def uses_celery_queue() -> bool:
    return get_settings().job_queue_backend == "celery"


def celery_runs_inline() -> bool:
    settings = get_settings()
    return settings.job_queue_backend == "sync" or settings.celery_task_always_eager


async def dispatch_consolidation(_session: AsyncSession, job_id: UUID, options: dict) -> None:
    if celery_runs_inline():
        from dendridb.services.consolidation import ConsolidationOptions
        from dendridb.workers.consolidation_worker import execute_consolidation_job

        await execute_consolidation_job(job_id, ConsolidationOptions(**options))
        return

    from dendridb.workers.tasks import consolidation_task

    consolidation_task.delay(str(job_id), options)


async def dispatch_decay(_session: AsyncSession, job_id: UUID, policy_payload: dict) -> None:
    if celery_runs_inline():
        from dendridb.workers.decay_worker import execute_decay_job

        await execute_decay_job(job_id, policy_payload)
        return

    from dendridb.workers.tasks import decay_task

    decay_task.delay(str(job_id), policy_payload)
