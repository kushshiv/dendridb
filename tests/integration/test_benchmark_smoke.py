import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_benchmark_smoke_suite_passes(integration_client):
    del integration_client

    from dendridb.benchmark.runner import run_benchmark_suite
    from dendridb.core.database import get_session_factory

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await run_benchmark_suite(
            session,
            namespace="bench-smoke",
            smoke=True,
            write_reports=False,
        )

    assert result.passed is True
    assert result.scenarios["ingestion"]["records_created"] == 3
    assert result.scenarios["recall"]["quality_hit_rate"] == 1.0
    assert result.scenarios["consolidation"]["job_status"] == "completed"
