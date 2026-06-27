"""Add episodes and episodic_events tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("namespace", sa.String(length=255), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("actor_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
    op.create_index("ix_episodes_namespace", "episodes", ["namespace"])
    op.create_index("ix_episodes_session_id", "episodes", ["session_id"])
    op.create_index("ix_episodes_task_id", "episodes", ["task_id"])
    op.create_index("ix_episodes_actor_id", "episodes", ["actor_id"])
    op.create_index("ix_episodes_namespace_session_id", "episodes", ["namespace", "session_id"])
    op.create_index("ix_episodes_namespace_created_at", "episodes", ["namespace", "created_at"])

    op.create_table(
        "episodic_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("episode_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["episode_id"], ["episodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "episode_id",
            "sequence_number",
            name="uq_episodic_events_episode_sequence",
        ),
    )
    op.create_index("ix_episodic_events_episode_id", "episodic_events", ["episode_id"])


def downgrade() -> None:
    op.drop_index("ix_episodic_events_episode_id", table_name="episodic_events")
    op.drop_table("episodic_events")
    op.drop_index("ix_episodes_namespace_created_at", table_name="episodes")
    op.drop_index("ix_episodes_namespace_session_id", table_name="episodes")
    op.drop_index("ix_episodes_actor_id", table_name="episodes")
    op.drop_index("ix_episodes_task_id", table_name="episodes")
    op.drop_index("ix_episodes_session_id", table_name="episodes")
    op.drop_index("ix_episodes_namespace", table_name="episodes")
    op.drop_table("episodes")
