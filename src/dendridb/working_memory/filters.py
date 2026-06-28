from datetime import UTC, datetime


class WorkingMemoryFilters:
    def __init__(
        self,
        *,
        namespace: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        include_expired: bool = False,
        limit: int = 50,
        offset: int = 0,
        now: datetime | None = None,
    ) -> None:
        self.namespace = namespace
        self.session_id = session_id
        self.task_id = task_id
        self.include_expired = include_expired
        self.limit = limit
        self.offset = offset
        self.now = now or datetime.now(UTC)
