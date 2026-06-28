from uuid import UUID

from dendridb.services.consolidation import ConsolidationOptions
from dendridb.workers.celery_app import celery_app
from dendridb.workers.consolidation_worker import run_consolidation_job_sync
from dendridb.workers.decay_worker import run_decay_job_sync


@celery_app.task(name="dendridb.consolidation.run")
def consolidation_task(job_id: str, options: dict) -> str:
    run_consolidation_job_sync(UUID(job_id), ConsolidationOptions(**options))
    return job_id


@celery_app.task(name="dendridb.decay.run")
def decay_task(job_id: str, policy_payload: dict) -> str:
    run_decay_job_sync(UUID(job_id), policy_payload)
    return job_id
