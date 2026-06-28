import asyncio
from uuid import UUID

from dendridb.core.database import get_session_factory
from dendridb.models.consolidation_job import ConsolidationJobRun
from dendridb.services.consolidation import (
    ConsolidationOptions,
    get_consolidation_job,
    run_consolidation_job,
)


async def execute_consolidation_job(
    job_id: UUID, options: ConsolidationOptions
) -> ConsolidationJobRun:
    session_factory = get_session_factory()
    async with session_factory() as session:
        job = await get_consolidation_job(session, job_id)
        if job is None:
            raise ValueError(f"Consolidation job {job_id} not found")
        return await run_consolidation_job(session, job, options)


def run_consolidation_job_sync(job_id: UUID, options: ConsolidationOptions) -> ConsolidationJobRun:
    return asyncio.run(execute_consolidation_job(job_id, options))
