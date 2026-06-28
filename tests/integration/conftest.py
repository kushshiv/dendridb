import os
import subprocess
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from dendridb.api.main import create_app
from dendridb.core.database import get_session_factory

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def run_migrations() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=PROJECT_ROOT,
    )


INTEGRATION_TABLES = (
    "decay_job_runs, consolidation_job_runs, memory_associations, semantic_evidence, "
    "semantic_memories, episodic_events, episodes, working_memory_items, memory_records"
)


def integration_enabled() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"


@pytest.fixture
async def integration_client():
    if not integration_enabled():
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 with PostgreSQL running to enable")

    run_migrations()

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(text(f"TRUNCATE TABLE {INTEGRATION_TABLES}"))
        await session.commit()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    async with session_factory() as session:
        await session.execute(text(f"TRUNCATE TABLE {INTEGRATION_TABLES}"))
        await session.commit()
