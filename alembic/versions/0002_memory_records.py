"""Add memory_records table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "memory_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("memory_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("salience", sa.Float(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_records_namespace", "memory_records", ["namespace"])
    op.create_index("ix_memory_records_actor_id", "memory_records", ["actor_id"])
    op.create_index("ix_memory_records_memory_type", "memory_records", ["memory_type"])
    op.create_index("ix_memory_records_source", "memory_records", ["source"])
    op.create_index(
        "ix_memory_records_namespace_created_at",
        "memory_records",
        ["namespace", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_memory_records_namespace_created_at", table_name="memory_records")
    op.drop_index("ix_memory_records_source", table_name="memory_records")
    op.drop_index("ix_memory_records_memory_type", table_name="memory_records")
    op.drop_index("ix_memory_records_actor_id", table_name="memory_records")
    op.drop_index("ix_memory_records_namespace", table_name="memory_records")
    op.drop_table("memory_records")
