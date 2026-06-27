from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MemoryNodeTypeLiteral = Literal[
    "memory_record",
    "episode",
    "episodic_event",
    "semantic_memory",
]

AssociationEdgeTypeLiteral = Literal[
    "related",
    "derived_from",
    "supports",
    "contradicts",
    "same_session",
    "metadata_match",
    "content_similar",
]


class AssociationCreate(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    source_type: MemoryNodeTypeLiteral
    source_id: UUID
    target_type: MemoryNodeTypeLiteral
    target_id: UUID
    edge_type: AssociationEdgeTypeLiteral = "related"
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    explanation: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_object(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("must be a JSON object")
        return value


class AutoLinkRequest(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    source_type: MemoryNodeTypeLiteral | None = None
    source_id: UUID | None = None
    metadata_match: bool = True
    content_similarity: bool = True
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    limit: int = Field(default=20, ge=1, le=200)


class AssociationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    source_type: str
    source_id: UUID
    target_type: str
    target_id: UUID
    edge_type: str
    weight: float
    explanation: str | None
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    created_at: datetime


class AssociationListResponse(BaseModel):
    items: list[AssociationResponse]
    total: int
    limit: int
    offset: int


class AutoLinkResponse(BaseModel):
    created: list[AssociationResponse]
    skipped: int


class RelatedMemoryQuery(BaseModel):
    namespace: str
    source_type: MemoryNodeTypeLiteral
    source_id: UUID
    depth: int = Field(default=1, ge=1, le=5)
    min_weight: float = Field(default=0.1, ge=0.0, le=1.0)
    limit: int = Field(default=50, ge=1, le=200)


class RelatedMemoryItem(BaseModel):
    node_type: str
    node_id: UUID
    depth: int
    path_weight: float
    explanation: str
    summary: dict[str, Any]


class RelatedMemoryResponse(BaseModel):
    source_type: str
    source_id: UUID
    items: list[RelatedMemoryItem]
