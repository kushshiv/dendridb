"""Add memory_associations table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edge_type", sa.String(length=64), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "namespace",
            "source_type",
            "source_id",
            "target_type",
            "target_id",
            "edge_type",
            name="uq_memory_associations_edge",
        ),
    )
    op.create_index("ix_memory_associations_namespace", "memory_associations", ["namespace"])
    op.create_index("ix_memory_associations_edge_type", "memory_associations", ["edge_type"])
    op.create_index(
        "ix_memory_associations_source",
        "memory_associations",
        ["namespace", "source_type", "source_id"],
    )
    op.create_index(
        "ix_memory_associations_target",
        "memory_associations",
        ["namespace", "target_type", "target_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_memory_associations_target", table_name="memory_associations")
    op.drop_index("ix_memory_associations_source", table_name="memory_associations")
    op.drop_index("ix_memory_associations_edge_type", table_name="memory_associations")
    op.drop_index("ix_memory_associations_namespace", table_name="memory_associations")
    op.drop_table("memory_associations")
