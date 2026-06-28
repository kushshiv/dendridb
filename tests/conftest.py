import os

os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "1")
os.environ.setdefault("WORKING_MEMORY_BACKEND", "redis")
os.environ.setdefault("JOB_QUEUE_BACKEND", "sync")

import pytest
from httpx import ASGITransport, AsyncClient

from dendridb.api.main import create_app
from dendridb.config import Settings, get_settings
from dendridb.core.database import clear_database_caches


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        environment="test",
        debug=True,
        postgres_host="localhost",
        postgres_port=5432,
        postgres_user="dendridb",
        postgres_password="dendridb",
        postgres_db="dendridb",
        celery_task_always_eager=True,
        working_memory_backend="redis",
        job_queue_backend="sync",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="dendridb",
    )


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    clear_database_caches()
    yield
    get_settings.cache_clear()
    clear_database_caches()


@pytest.fixture
def app(test_settings: Settings, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "1")
    get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
