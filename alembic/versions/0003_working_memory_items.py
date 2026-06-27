"""Add working_memory_items table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "working_memory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ttl_seconds", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint(
            "namespace",
            "session_id",
            "key",
            name="uq_working_memory_namespace_session_key",
        ),
    )
    op.create_index("ix_working_memory_items_namespace", "working_memory_items", ["namespace"])
    op.create_index(
        "ix_working_memory_items_session_id",
        "working_memory_items",
        ["session_id"],
    )
    op.create_index("ix_working_memory_items_task_id", "working_memory_items", ["task_id"])
    op.create_index("ix_working_memory_items_actor_id", "working_memory_items", ["actor_id"])
    op.create_index("ix_working_memory_items_expires_at", "working_memory_items", ["expires_at"])
    op.create_index(
        "ix_working_memory_namespace_session_id",
        "working_memory_items",
        ["namespace", "session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_working_memory_namespace_session_id", table_name="working_memory_items")
    op.drop_index("ix_working_memory_items_expires_at", table_name="working_memory_items")
    op.drop_index("ix_working_memory_items_actor_id", table_name="working_memory_items")
    op.drop_index("ix_working_memory_items_task_id", table_name="working_memory_items")
    op.drop_index("ix_working_memory_items_session_id", table_name="working_memory_items")
    op.drop_index("ix_working_memory_items_namespace", table_name="working_memory_items")
    op.drop_table("working_memory_items")
