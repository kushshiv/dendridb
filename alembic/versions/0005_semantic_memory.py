"""Add semantic_memories and semantic_evidence tables.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semantic_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("superseded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["superseded_by_id"], ["semantic_memories.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_semantic_memories_namespace", "semantic_memories", ["namespace"])
    op.create_index("ix_semantic_memories_key", "semantic_memories", ["key"])
    op.create_index("ix_semantic_memories_status", "semantic_memories", ["status"])
    op.create_index("ix_semantic_memories_actor_id", "semantic_memories", ["actor_id"])
    op.create_index(
        "ix_semantic_memories_namespace_key_status",
        "semantic_memories",
        ["namespace", "key", "status"],
    )
    op.create_index(
        "ix_semantic_memories_namespace_created_at",
        "semantic_memories",
        ["namespace", "created_at"],
    )

    op.create_table(
        "semantic_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semantic_memory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["semantic_memory_id"], ["semantic_memories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "semantic_memory_id",
            "source_type",
            "source_id",
            name="uq_semantic_evidence_source",
        ),
    )
    op.create_index(
        "ix_semantic_evidence_semantic_memory_id",
        "semantic_evidence",
        ["semantic_memory_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_semantic_evidence_semantic_memory_id", table_name="semantic_evidence")
    op.drop_table("semantic_evidence")
    op.drop_index("ix_semantic_memories_namespace_created_at", table_name="semantic_memories")
    op.drop_index("ix_semantic_memories_namespace_key_status", table_name="semantic_memories")
    op.drop_index("ix_semantic_memories_actor_id", table_name="semantic_memories")
    op.drop_index("ix_semantic_memories_status", table_name="semantic_memories")
    op.drop_index("ix_semantic_memories_key", table_name="semantic_memories")
    op.drop_index("ix_semantic_memories_namespace", table_name="semantic_memories")
    op.drop_table("semantic_memories")
