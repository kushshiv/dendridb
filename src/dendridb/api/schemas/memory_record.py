from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemoryRecordCreate(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    actor_id: str | None = Field(default=None, max_length=255)
    memory_type: str = Field(default="generic", min_length=1, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str | None = Field(default=None, max_length=255)
    provenance: dict[str, Any] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    salience: float | None = Field(default=None, ge=0.0)

    @field_validator("metadata", "provenance")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class MemoryRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    actor_id: str | None
    memory_type: str
    content: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    source: str | None
    provenance: dict[str, Any] | None
    confidence: float | None
    salience: float | None
    created_at: datetime
    updated_at: datetime


class MemoryRecordListResponse(BaseModel):
    items: list[MemoryRecordResponse]
    total: int
    limit: int
    offset: int
