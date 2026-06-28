import os
import subprocess
import sys

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")
os.environ.setdefault("WORKING_MEMORY_BACKEND", "redis")
os.environ.setdefault("JOB_QUEUE_BACKEND", "sync")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from dendridb.api.main import create_app
from dendridb.config.settings import get_settings
from dendridb.core.database import get_session_factory
from dendridb.core.redis_client import flush_working_memory_keys
from dendridb.graph.neo4j_store import flush_neo4j_graph

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


async def _reset_stores() -> None:
    get_settings.cache_clear()
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(text(f"TRUNCATE TABLE {INTEGRATION_TABLES}"))
        await session.commit()
    if get_settings().working_memory_backend == "redis":
        await flush_working_memory_keys()
    await flush_neo4j_graph()


@pytest.fixture
async def integration_client():
    if not integration_enabled():
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 with PostgreSQL running to enable")

    run_migrations()
    await _reset_stores()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await _reset_stores()
