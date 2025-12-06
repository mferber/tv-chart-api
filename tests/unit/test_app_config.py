import pytest

from exceptions import ConfigurationError


def test_env_jwt_secret_is_required(monkeypatch):
    monkeypatch.delenv("JWT_ENCODING_SECRET")

    with pytest.raises(ConfigurationError):
        from app import app  # noqa F401
