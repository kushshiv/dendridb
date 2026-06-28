from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DecayRunRequest(BaseModel):
    namespace: str = Field(..., min_length=1, max_length=255)
    half_life_hours: float | None = Field(default=None, gt=0.0)
    min_salience: float | None = Field(default=None, ge=0.0)
    dry_run: bool = False


class DecayStats(BaseModel):
    records_scanned: int = 0
    records_decayed: int = 0
    records_archived: int = 0
    records_skipped_pinned: int = 0


class DecayJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    namespace: str
    status: str
    trigger: str
    dry_run: bool
    stats: DecayStats
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class DecayJobListResponse(BaseModel):
    items: list[DecayJobResponse]
    total: int
    limit: int
    offset: int
