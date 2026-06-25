import pytest

from dendridb.config import Settings, get_settings


@pytest.mark.unit
def test_settings_defaults():
    settings = Settings()
    assert settings.app_name == "DendriDB"
    assert settings.postgres_user == "dendridb"
    assert settings.postgres_db == "dendridb"


@pytest.mark.unit
def test_database_url_format(test_settings: Settings):
    url = test_settings.database_url
    assert url.startswith("postgresql+psycopg://")
    assert "dendridb" in url


@pytest.mark.unit
def test_get_settings_cached(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ENVIRONMENT", "cached-test")
    get_settings.cache_clear()
    first = get_settings()
    second = get_settings()
    assert first is second
    assert first.environment == "cached-test"
