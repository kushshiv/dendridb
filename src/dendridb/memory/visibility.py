"""Memory visibility helpers for recall and listing."""

from __future__ import annotations

from datetime import datetime

from dendridb.memory.consolidation import is_merged_record


def is_archived_record(archived_at: datetime | None) -> bool:
    return archived_at is not None


def is_active_memory(*, metadata: dict, archived_at: datetime | None) -> bool:
    if is_merged_record(metadata):
        return False
    return not is_archived_record(archived_at)
