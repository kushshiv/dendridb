from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class WorkingMemoryRecord:
    id: UUID
    namespace: str
    session_id: str
    task_id: str | None
    key: str
    actor_id: str | None
    content: str
    metadata_: dict[str, Any]
    ttl_seconds: int | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkingMemoryConflictError(Exception):
    """Raised when a session key already exists."""
