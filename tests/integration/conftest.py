import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from dendridb.api.main import create_app
from dendridb.core.database import Base, get_engine, get_session_factory

INTEGRATION_TABLES = (
    "memory_associations, semantic_evidence, semantic_memories, episodic_events, episodes, "
    "working_memory_items, memory_records"
)


def integration_enabled() -> bool:
    return os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"


@pytest.fixture
async def integration_client():
    if not integration_enabled():
        pytest.skip("Set RUN_INTEGRATION_TESTS=1 with PostgreSQL running to enable")

    engine = get_engine()
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)

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
