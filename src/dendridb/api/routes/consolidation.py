from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.consolidation import (
    ConsolidationJobListResponse,
    ConsolidationJobResponse,
    ConsolidationRunRequest,
    ConsolidationStats,
)
from dendridb.core.database import get_db_session
from dendridb.services.consolidation import (
    get_consolidation_job,
    list_consolidation_jobs,
    start_consolidation,
)

router = APIRouter(prefix="/consolidation", tags=["consolidation"])


def _to_response(job) -> ConsolidationJobResponse:
    stats = ConsolidationStats.model_validate(job.stats or {})
    return ConsolidationJobResponse(
        id=job.id,
        namespace=job.namespace,
        status=job.status,
        trigger=job.trigger,
        dry_run=job.dry_run,
        stats=stats,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs", response_model=ConsolidationJobResponse, status_code=status.HTTP_201_CREATED)
async def run_consolidation_route(
    payload: ConsolidationRunRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ConsolidationJobResponse:
    job = await start_consolidation(session, payload, trigger="api")
    return _to_response(job)


@router.get("/jobs/{job_id}", response_model=ConsolidationJobResponse)
async def get_consolidation_job_route(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ConsolidationJobResponse:
    job = await get_consolidation_job(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consolidation job {job_id} not found",
        )
    return _to_response(job)


@router.get("/jobs", response_model=ConsolidationJobListResponse)
async def list_consolidation_jobs_route(
    namespace: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ConsolidationJobListResponse:
    jobs, total = await list_consolidation_jobs(
        session,
        namespace=namespace,
        limit=limit,
        offset=offset,
    )
    return ConsolidationJobListResponse(
        items=[_to_response(job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )
