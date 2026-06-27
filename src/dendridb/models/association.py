import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from dendridb.core.database import Base


class MemoryNodeType(StrEnum):
    MEMORY_RECORD = "memory_record"
    EPISODE = "episode"
    EPISODIC_EVENT = "episodic_event"
    SEMANTIC_MEMORY = "semantic_memory"


class AssociationEdgeType(StrEnum):
    RELATED = "related"
    DERIVED_FROM = "derived_from"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    SAME_SESSION = "same_session"
    METADATA_MATCH = "metadata_match"
    CONTENT_SIMILAR = "content_similar"


class MemoryAssociation(Base):
    """Directed edge connecting two memory nodes."""

    __tablename__ = "memory_associations"
    __table_args__ = (
        UniqueConstraint(
            "namespace",
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            "edge_type",
            name="uq_memory_associations_edge",
        ),
        Index(
            "ix_memory_associations_source",
            "namespace",
            "source_type",
            "source_id",
        ),
        Index(
            "ix_memory_associations_target",
            "namespace",
            "target_type",
            "target_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
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
