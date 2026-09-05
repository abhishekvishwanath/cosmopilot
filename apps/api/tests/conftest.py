import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture(autouse=True)
def _isolate_from_local_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Settings() reads apps/api/.env by default (see core/config.py). Without
    this, a developer's real local .env — e.g. actual Supabase credentials —
    would silently leak into every test's "unconfigured" / "not set" cases,
    making test results depend on whatever happens to be in that file.
    Tests control Settings entirely via explicit kwargs or monkeypatched
    env vars instead.
    """
    monkeypatch.setitem(Settings.model_config, "env_file", None)


@pytest.fixture
def client() -> TestClient:
    get_settings.cache_clear()
    return TestClient(app)
