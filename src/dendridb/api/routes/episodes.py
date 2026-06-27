from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dendridb.api.schemas.episode import (
    EpisodeCreate,
    EpisodeListResponse,
    EpisodeReplayResponse,
    EpisodeResponse,
    EpisodicEventCreate,
    EpisodicEventResponse,
    build_episode_response,
)
from dendridb.core.database import get_db_session
from dendridb.services.episode import (
    EpisodeFilters,
    append_episodic_event,
    count_episode_events,
    create_episode,
    get_episode,
    list_episodes,
    replay_episode,
)

router = APIRouter(prefix="/episodes", tags=["episodes"])


@router.post("", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode_route(
    payload: EpisodeCreate,
    session: AsyncSession = Depends(get_db_session),
) -> EpisodeResponse:
    episode = await create_episode(session, payload)
    return build_episode_response(episode, event_count=0)


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode_route(
    episode_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> EpisodeResponse:
    episode = await get_episode(session, episode_id)
    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found",
        )
    count = await count_episode_events(session, episode_id)
    return build_episode_response(episode, event_count=count)


@router.get("/{episode_id}/replay", response_model=EpisodeReplayResponse)
async def replay_episode_route(
    episode_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> EpisodeReplayResponse:
    replay = await replay_episode(session, episode_id)
    if replay is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found",
        )
    episode, events = replay
    return EpisodeReplayResponse(
        episode=build_episode_response(episode, event_count=len(events)),
        events=[EpisodicEventResponse.model_validate(event) for event in events],
    )


@router.post(
    "/{episode_id}/events",
    response_model=EpisodicEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def append_event_route(
    episode_id: UUID,
    payload: EpisodicEventCreate,
    session: AsyncSession = Depends(get_db_session),
) -> EpisodicEventResponse:
    event = await append_episodic_event(session, episode_id, payload)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode {episode_id} not found",
        )
    return EpisodicEventResponse.model_validate(event)


@router.get("", response_model=EpisodeListResponse)
async def list_episodes_route(
    namespace: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    task_id: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> EpisodeListResponse:
    filters = EpisodeFilters(
        namespace=namespace,
        session_id=session_id,
        task_id=task_id,
        actor_id=actor_id,
        limit=limit,
        offset=offset,
    )
    episodes, total = await list_episodes(session, filters)
    items = []
    for episode in episodes:
        count = await count_episode_events(session, episode.id)
        items.append(build_episode_response(episode, event_count=count))
    return EpisodeListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
