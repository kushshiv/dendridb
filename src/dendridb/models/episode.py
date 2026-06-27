import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dendridb.core.database import Base

if TYPE_CHECKING:
    from dendridb.models.episodic_event import EpisodicEvent


class Episode(Base):
    """A grouped sequence of related experiential events."""

    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_namespace_session_id", "namespace", "session_id"),
        Index("ix_episodes_namespace_created_at", "namespace", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
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

    events: Mapped[list["EpisodicEvent"]] = relationship(
        back_populates="episode",
        order_by="EpisodicEvent.sequence_number",
        cascade="all, delete-orphan",
    )
