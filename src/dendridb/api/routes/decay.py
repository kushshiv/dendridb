from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.decay import (
    DecayJobListResponse,
    DecayJobResponse,
    DecayRunRequest,
    DecayStats,
)
from dendridb.core.database import get_db_session
from dendridb.services.decay import get_decay_job, list_decay_jobs, start_decay

router = APIRouter(prefix="/decay", tags=["decay"])


def _to_response(job) -> DecayJobResponse:
    return DecayJobResponse(
        id=job.id,
        namespace=job.namespace,
        status=job.status,
        trigger=job.trigger,
        dry_run=job.dry_run,
        stats=DecayStats.model_validate(job.stats or {}),
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs", response_model=DecayJobResponse, status_code=status.HTTP_201_CREATED)
async def run_decay_route(
    payload: DecayRunRequest,
    session: AsyncSession = Depends(get_db_session),
) -> DecayJobResponse:
    job = await start_decay(session, payload, trigger="api")
    return _to_response(job)


@router.get("/jobs/{job_id}", response_model=DecayJobResponse)
async def get_decay_job_route(
    job_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DecayJobResponse:
    job = await get_decay_job(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decay job {job_id} not found",
        )
    return _to_response(job)


@router.get("/jobs", response_model=DecayJobListResponse)
async def list_decay_jobs_route(
    namespace: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> DecayJobListResponse:
    jobs, total = await list_decay_jobs(
        session,
        namespace=namespace,
        limit=limit,
        offset=offset,
    )
    return DecayJobListResponse(
        items=[_to_response(job) for job in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )
