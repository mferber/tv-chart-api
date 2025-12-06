import pytest

from exceptions import ConfigurationError


def test_env_jwt_secret_is_required(monkeypatch):
    monkeypatch.delenv("JWT_ENCODING_SECRET")
    with pytest.raises(ConfigurationError):
        from app import app  # noqa F401


@pytest.mark.parametrize(
    "env_var",
    [
        "DEV_DB_DRIVER",
        "DEV_DB_USER",
        "DEV_DB_PASS",
        "DEV_DB_HOST",
        "DEV_DB_PORT",
        "DEV_DB_NAME",
    ],
)
def test_env_db_settings_are_required(env_var, monkeypatch):
    monkeypatch.delenv(env_var)
    with pytest.raises(ConfigurationError):
        from app import app  # noqa F401
