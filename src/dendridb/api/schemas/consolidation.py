from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConsolidationRunRequest(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    lookback_hours: int = Field(default=168, ge=1, le=8760)
    duplicate_similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    min_pattern_occurrences: int = Field(default=2, ge=2, le=100)
    dry_run: bool = False


class ConsolidationStats(BaseModel):
    episodes_replayed: int = 0
    events_replayed: int = 0
    duplicates_merged: int = 0
    patterns_promoted: int = 0
    patterns_merged: int = 0
    promotion_actions: list[str] = Field(default_factory=list)
    duplicate_pairs: list[dict[str, str | float]] = Field(default_factory=list)


class ConsolidationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    status: str
    trigger: str
    dry_run: bool
    stats: ConsolidationStats
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ConsolidationJobListResponse(BaseModel):
    items: list[ConsolidationJobResponse]
    total: int
    limit: int
    offset: int
