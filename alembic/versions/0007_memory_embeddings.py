"""Add pgvector extension and memory record embeddings.

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-26

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE memory_records ADD COLUMN embedding vector(384)")
    op.execute(
        "CREATE INDEX ix_memory_records_embedding "
        "ON memory_records USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_memory_records_embedding")
    op.drop_column("memory_records", "embedding")
