import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dendridb.core.database import Base


class WorkingMemoryItem(Base):
    """Short-term session-scoped working memory."""

    __tablename__ = "working_memory_items"
    __table_args__ = (
        UniqueConstraint(
            "namespace",
            "session_id",
            "key",
            name="uq_working_memory_namespace_session_key",
        ),
        Index("ix_working_memory_namespace_session_id", "namespace", "session_id"),
        Index("ix_working_memory_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    ttl_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
