import asyncio
import os
import subprocess
import sys
import time

import pytest
from httpx import ASGITransport, AsyncClient

from dendridb.api.main import create_app
from dendridb.core.database import get_session_factory

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

E2E_TABLES = (
    "decay_job_runs, consolidation_job_runs, memory_associations, semantic_evidence, "
    "semantic_memories, episodic_events, episodes, working_memory_items, memory_records"
)


def e2e_enabled() -> bool:
    return os.getenv("RUN_E2E_TESTS", "0") == "1"


def e2e_live_mode() -> bool:
    return os.getenv("E2E_LIVE", "0") == "1"


def e2e_base_url() -> str:
    return os.getenv("E2E_BASE_URL", "http://localhost:8000")


def run_migrations() -> None:
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        cwd=PROJECT_ROOT,
    )


async def wait_for_live_api(base_url: str, *, timeout_seconds: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    async with AsyncClient(base_url=base_url, timeout=5.0) as probe:
        while time.monotonic() < deadline:
            try:
                response = await probe.get("/health/ready")
                if response.status_code == 200:
                    return
            except Exception as exc:
                last_error = exc
            await asyncio.sleep(0.5)

    detail = f"API not ready at {base_url}"
    if last_error is not None:
        detail = f"{detail}: {last_error}"
    raise RuntimeError(detail)


async def _truncate_tables() -> None:
    from sqlalchemy import text

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(text(f"TRUNCATE TABLE {E2E_TABLES}"))
        await session.commit()


@pytest.fixture
async def e2e_client():
    if not e2e_enabled():
        pytest.skip("Set RUN_E2E_TESTS=1 to enable end-to-end tests")

    if e2e_live_mode():
        base_url = e2e_base_url()
        await wait_for_live_api(base_url)
        async with AsyncClient(base_url=base_url, timeout=30.0) as client:
            yield client
        return

    run_migrations()
    await _truncate_tables()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
        yield client

    await _truncate_tables()
