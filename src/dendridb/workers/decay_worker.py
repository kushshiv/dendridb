import asyncio
from uuid import UUID

from dendridb.core.database import get_session_factory
from dendridb.models.decay_job import DecayJobRun
from dendridb.services.decay import get_decay_job, policy_from_settings, run_decay_job


async def execute_decay_job(job_id: UUID, policy_payload: dict) -> DecayJobRun:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job = await get_decay_job(session, job_id)
        if job is None:
            raise ValueError(f"Decay job {job_id} not found")
        from dendridb.api.schemas.decay import DecayRunRequest

        policy = policy_from_settings(DecayRunRequest(**policy_payload))
        return await run_decay_job(session, job, policy)


def run_decay_job_sync(job_id: UUID, policy_payload: dict) -> DecayJobRun:
    return asyncio.run(execute_decay_job(job_id, policy_payload))
