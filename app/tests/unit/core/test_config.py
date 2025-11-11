from app.core.config import Settings
import pytest

@pytest.fixture
def env_vars(monkeypatch):
    """ Mock a .env file with environment variables"""
    env_data = {
        "DATABASE_URL": "postgres://user:pass@localhost/db",
        "MONGO_URL": "mongodb://localhost:27017",
        "MONGO_DB": "py-learnstream",
        "MUX_TOKEN_ID": "mux_id",
        "MUX_TOKEN_SECRET": "mux_secret",
        "MUX_WEBHOOK_SECRET": "mux_webhook",
        "REDIS_URL": "redis://localhost:6379/0",
        "JWT_SECRET": "supersecret",
    }
    for k, v in env_data.items():
        monkeypatch.setenv(k, v)
    return env_data

def test_settings_loads_env_variables(env_vars):
    """ Should load environment variables correctly."""
    settings = Settings()
    assert settings.DATABASE_URL == env_vars["DATABASE_URL"]


def test_settings_env_file_config():
    """ Ensure model_config uses .env and ignores extra fields."""
    s = Settings()
    assert s.model_config["env_file"] == ".env"
    assert s.model_config["extra"] == "ignore"

def test_settings_handles_missing_env(monkeypatch):
    """Ensure missing variables use defaults instead of breaking."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings()
    assert settings.DATABASE_URL is not None  # uses default from config

