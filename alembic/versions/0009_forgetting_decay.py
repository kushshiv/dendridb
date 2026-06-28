"""Add forgetting/decay columns and decay job runs.

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    memory_columns = {column["name"] for column in inspector.get_columns("memory_records")}

    if "pinned" not in memory_columns:
        op.add_column(
            "memory_records",
            sa.Column("pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("memory_records", "pinned", server_default=None)
    if "archived_at" not in memory_columns:
        op.add_column(
            "memory_records",
            sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "last_retrieved_at" not in memory_columns:
        op.add_column(
            "memory_records",
            sa.Column("last_retrieved_at", sa.DateTime(timezone=True), nullable=True),
        )

    if "decay_job_runs" not in inspector.get_table_names():
        op.create_table(
            "decay_job_runs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("namespace", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("trigger", sa.String(length=32), nullable=False),
            sa.Column("dry_run", sa.Boolean(), nullable=False),
            sa.Column("stats", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_decay_job_runs_namespace", "decay_job_runs", ["namespace"])
        op.create_index("ix_decay_job_runs_status", "decay_job_runs", ["status"])
    else:
        index_names = {index["name"] for index in inspector.get_indexes("decay_job_runs")}
        if "ix_decay_job_runs_namespace" not in index_names:
            op.create_index("ix_decay_job_runs_namespace", "decay_job_runs", ["namespace"])
        if "ix_decay_job_runs_status" not in index_names:
            op.create_index("ix_decay_job_runs_status", "decay_job_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_decay_job_runs_status", table_name="decay_job_runs")
    op.drop_index("ix_decay_job_runs_namespace", table_name="decay_job_runs")
    op.drop_table("decay_job_runs")
    op.drop_column("memory_records", "last_retrieved_at")
    op.drop_column("memory_records", "archived_at")
    op.drop_column("memory_records", "pinned")
