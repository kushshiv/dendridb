from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dendridb.models.semantic_memory import SemanticMemory


class EvidenceLinkCreate(BaseModel):
    source_type: Literal["memory_record", "episode", "episodic_event"]
    source_id: UUID


class SemanticMemoryCreate(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    key: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    actor_id: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] | None = None
    evidence: list[EvidenceLinkCreate] = Field(default_factory=list)

    @field_validator("metadata", "provenance")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class SemanticMemoryPromote(SemanticMemoryCreate):
    """Same payload as direct create; promotion rules apply on write."""


class EvidenceLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    source_id: UUID
    created_at: datetime


class SemanticMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    key: str
    content: str
    confidence: float
    version: int
    status: str
    superseded_by_id: UUID | None
    actor_id: str | None
    source: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    provenance: dict[str, Any] | None
    evidence_count: int = 0
    created_at: datetime
    updated_at: datetime


class SemanticMemoryListResponse(BaseModel):
    items: list[SemanticMemoryResponse]
    total: int
    limit: int
    offset: int


class SemanticMemoryPromoteResponse(BaseModel):
    memory: SemanticMemoryResponse
    action: Literal["created", "merged", "versioned"]


class SemanticMemoryEvidenceResponse(BaseModel):
    items: list[EvidenceLinkResponse]


def build_semantic_memory_response(
    memory: SemanticMemory,
    evidence_count: int,
) -> SemanticMemoryResponse:
    return SemanticMemoryResponse.model_validate(memory).model_copy(
        update={"evidence_count": evidence_count}
    )
