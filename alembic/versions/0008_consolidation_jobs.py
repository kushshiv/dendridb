"""Add consolidation_job_runs table.

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "consolidation_job_runs",
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
    op.create_index("ix_consolidation_job_runs_namespace", "consolidation_job_runs", ["namespace"])
    op.create_index("ix_consolidation_job_runs_status", "consolidation_job_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_consolidation_job_runs_status", table_name="consolidation_job_runs")
    op.drop_index("ix_consolidation_job_runs_namespace", table_name="consolidation_job_runs")
    op.drop_table("consolidation_job_runs")
