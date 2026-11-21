import pytest
from pydantic import ValidationError

from app.utils.config import Settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ["DEBUG", "AUTH_ENABLED", "SECRET_KEY", "DATABASE_URL", "CORS_ALLOWED_ORIGINS"]:
        monkeypatch.delenv(key, raising=False)


def test_production_settings_reject_development_defaults():
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, environment="production")

    message = str(error.value)
    assert "SECRET_KEY" in message
    assert "DATABASE_URL" in message
    assert "DEBUG=false" in message
    assert "CORS_ALLOWED_ORIGINS" in message


def test_production_settings_accept_explicit_secure_values():
    settings = Settings(
        _env_file=None,
        environment="production",
        debug=False,
        secret_key="a" * 48,
        database_url="postgresql://clearhire:unique-db-password@postgres:5432/clearhire",
        cors_allowed_origins="https://clearhire.example.com",
    )

    assert settings.environment == "production"
    assert settings.auth_enabled is True


@pytest.mark.parametrize(
    ("setting_name", "setting_value", "expected_error"),
    [
        ("auth_enabled", False, "AUTH_ENABLED=true"),
        ("cors_allowed_origins", "http://clearhire.example.com", "CORS_ALLOWED_ORIGINS"),
    ],
)
def test_production_settings_reject_unsafe_auth_or_cors(setting_name, setting_value, expected_error):
    config = {
        "_env_file": None,
        "environment": "production",
        "debug": False,
        "secret_key": "a" * 48,
        "database_url": "postgresql://clearhire:unique-db-password@postgres:5432/clearhire",
        "cors_allowed_origins": "https://clearhire.example.com",
        setting_name: setting_value,
    }

    with pytest.raises(ValidationError) as error:
        Settings(**config)

    assert expected_error in str(error.value)
