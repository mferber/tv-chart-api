import os

import pytest
from dotenv import load_dotenv

from create_app import create_app
from exceptions import ConfigurationError


# Load .env into the environment, then unset the named variable; monkeypatch the
# app_config module to indicate that the config has already been loaded
def _omit_from_loaded_env(
    env_var_names: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import app_config

    load_dotenv()

    # prevent config reloading at app startup
    monkeypatch.setattr(app_config, "load", lambda: None)
    monkeypatch.setattr(app_config, "check_loaded", lambda: None)

    for env_var_name in env_var_names:
        os.environ.pop(env_var_name, None)


def test_env_jwt_secret_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    env_var = "JWT_ENCODING_SECRET"
    _omit_from_loaded_env([env_var], monkeypatch)
    with pytest.raises(ConfigurationError, match=env_var):
        create_app()


def test_database_url_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    _omit_from_loaded_env(["DATABASE_URL"], monkeypatch)
    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        create_app()


def test_cors_allowed_origins_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    _omit_from_loaded_env(["CORS_ALLOWED_ORIGINS"], monkeypatch)
    with pytest.raises(ConfigurationError, match="CORS_ALLOWED_ORIGINS"):
        create_app()


def test_cors_allowed_origins_must_be_valid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _omit_from_loaded_env(["CORS_ALLOWED_ORIGINS"], monkeypatch)
    os.environ["CORS_ALLOWED_ORIGINS"] = "foo"
    with pytest.raises(ConfigurationError, match="CORS_ALLOWED_ORIGINS"):
        create_app()


def test_cors_allowed_origins_cannot_be_nonlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _omit_from_loaded_env(["CORS_ALLOWED_ORIGINS"], monkeypatch)
    os.environ["CORS_ALLOWED_ORIGINS"] = "{}"
    with pytest.raises(ConfigurationError, match="CORS_ALLOWED_ORIGINS"):
        create_app()


def test_cors_allowed_origins_cannot_be_empty_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _omit_from_loaded_env(["CORS_ALLOWED_ORIGINS"], monkeypatch)
    os.environ["CORS_ALLOWED_ORIGINS"] = "[]"
    with pytest.raises(ConfigurationError, match="CORS_ALLOWED_ORIGINS"):
        create_app()


def test_cors_allowed_origins_cannot_contain_nonstrings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _omit_from_loaded_env(["CORS_ALLOWED_ORIGINS"], monkeypatch)
    os.environ["CORS_ALLOWED_ORIGINS"] = '["abc", 1]'
    with pytest.raises(ConfigurationError, match="CORS_ALLOWED_ORIGINS"):
        create_app()


def test_cors_allowed_origins_is_list_of_strings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _omit_from_loaded_env(["CORS_ALLOWED_ORIGINS"], monkeypatch)
    os.environ["CORS_ALLOWED_ORIGINS"] = '["abc", "def"]'
    create_app()
