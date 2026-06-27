from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkingMemoryCreate(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    session_id: str = Field(..., min_length=1, max_length=255)
    key: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    task_id: str | None = Field(default=None, max_length=255)
    actor_id: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int | None = Field(default=None, ge=1)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class WorkingMemoryReplace(WorkingMemoryCreate):
    """Upsert working memory for a session key."""


class WorkingMemoryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    task_id: str | None = Field(default=None, max_length=255)
    actor_id: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] | None = None
    ttl_seconds: int | None = Field(default=None, ge=1)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class WorkingMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    session_id: str
    task_id: str | None
    key: str
    actor_id: str | None
    content: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    ttl_seconds: int | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkingMemoryListResponse(BaseModel):
    items: list[WorkingMemoryResponse]
    total: int
    limit: int
    offset: int
