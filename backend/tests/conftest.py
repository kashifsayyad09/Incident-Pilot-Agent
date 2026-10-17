import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    for k in ("INCIDENTPILOT_MODE", "INCIDENTPILOT_API_KEY", "INCIDENTPILOT_CORS_ORIGINS"):
        monkeypatch.delenv(k, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    return TestClient(create_app())
