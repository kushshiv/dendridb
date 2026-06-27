from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dendridb.api.schemas.episode import EpisodeCreate, EpisodicEventCreate
from dendridb.models.episode import Episode
from dendridb.models.episodic_event import EpisodicEvent


class EpisodeFilters:
    def __init__(
        self,
        *,
        namespace: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        actor_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        self.namespace = namespace
        self.session_id = session_id
        self.task_id = task_id
        self.actor_id = actor_id
        self.limit = limit
        self.offset = offset


def _apply_episode_filters(query, filters: EpisodeFilters):
    if filters.namespace is not None:
        query = query.where(Episode.namespace == filters.namespace)
    if filters.session_id is not None:
        query = query.where(Episode.session_id == filters.session_id)
    if filters.task_id is not None:
        query = query.where(Episode.task_id == filters.task_id)
    if filters.actor_id is not None:
        query = query.where(Episode.actor_id == filters.actor_id)
    return query


async def count_episode_events(session: AsyncSession, episode_id: UUID) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(EpisodicEvent)
        .where(EpisodicEvent.episode_id == episode_id)
    )
    return int(result.scalar_one())


async def create_episode(session: AsyncSession, payload: EpisodeCreate) -> Episode:
    episode = Episode(
        namespace=payload.namespace,
        session_id=payload.session_id,
        task_id=payload.task_id,
        actor_id=payload.actor_id,
        title=payload.title,
        summary=payload.summary,
        metadata_=payload.metadata,
    )
    session.add(episode)
    await session.commit()
    await session.refresh(episode)
    return episode


async def get_episode(session: AsyncSession, episode_id: UUID) -> Episode | None:
    return await session.get(Episode, episode_id)


async def list_episodes(
    session: AsyncSession,
    filters: EpisodeFilters,
) -> tuple[list[Episode], int]:
    filtered_query = _apply_episode_filters(select(Episode), filters)

    count_query = select(func.count()).select_from(filtered_query.subquery())
    total = int((await session.execute(count_query)).scalar_one())

    list_query = (
        _apply_episode_filters(select(Episode), filters)
        .order_by(Episode.created_at.desc())
        .limit(filters.limit)
        .offset(filters.offset)
    )
    result = await session.execute(list_query)
    return list(result.scalars().all()), total


async def append_episodic_event(
    session: AsyncSession,
    episode_id: UUID,
    payload: EpisodicEventCreate,
) -> EpisodicEvent | None:
    episode = await session.get(Episode, episode_id)
    if episode is None:
        return None

    result = await session.execute(
        select(func.coalesce(func.max(EpisodicEvent.sequence_number), -1)).where(
            EpisodicEvent.episode_id == episode_id
        )
    )
    next_sequence = int(result.scalar_one()) + 1

    event = EpisodicEvent(
        episode_id=episode_id,
        sequence_number=next_sequence,
        event_type=payload.event_type,
        content=payload.content,
        metadata_=payload.metadata,
        source=payload.source,
        provenance=payload.provenance,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def replay_episode(
    session: AsyncSession,
    episode_id: UUID,
) -> tuple[Episode, list[EpisodicEvent]] | None:
    query = select(Episode).where(Episode.id == episode_id).options(selectinload(Episode.events))
    result = await session.execute(query)
    episode = result.scalar_one_or_none()
    if episode is None:
        return None

    events = sorted(episode.events, key=lambda event: event.sequence_number)
    return episode, events
