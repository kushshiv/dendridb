from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dendridb.models.episode import Episode


class EpisodeCreate(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    session_id: str = Field(..., min_length=1, max_length=255)
    task_id: str | None = Field(default=None, max_length=255)
    actor_id: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=512)
    summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class EpisodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    session_id: str
    task_id: str | None
    actor_id: str | None
    title: str | None
    summary: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    event_count: int = 0
    created_at: datetime
    updated_at: datetime


class EpisodeListResponse(BaseModel):
    items: list[EpisodeResponse]
    total: int
    limit: int
    offset: int


class EpisodicEventCreate(BaseModel):
    content: str = Field(..., min_length=1)
    event_type: str = Field(default="event", min_length=1, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = Field(default=None, max_length=255)
    provenance: dict[str, Any] | None = None

    @field_validator("metadata", "provenance")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class EpisodicEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    episode_id: UUID
    sequence_number: int
    event_type: str
    content: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    source: str | None
    provenance: dict[str, Any] | None
    created_at: datetime


class EpisodeReplayResponse(BaseModel):
    episode: EpisodeResponse
    events: list[EpisodicEventResponse]


def build_episode_response(episode: Episode, event_count: int) -> EpisodeResponse:
    return EpisodeResponse.model_validate(episode).model_copy(update={"event_count": event_count})
