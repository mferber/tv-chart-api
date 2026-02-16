import os

import pytest
from dotenv import load_dotenv

from create_app import create_app
from exceptions import ConfigurationError


# Load .env into the environment, then unset the named variable; monkeypatch the
# app_config module to indicate that the config has already been loaded
def _omit_from_loaded_env(env_var_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    import app_config

    load_dotenv()

    # prevent config reloading at app startup
    monkeypatch.setattr(app_config, "load", lambda: None)
    monkeypatch.setattr(app_config, "check_loaded", lambda: None)

    os.environ.pop(env_var_name, None)


def test_env_jwt_secret_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    env_var = "JWT_ENCODING_SECRET"
    _omit_from_loaded_env(env_var, monkeypatch)
    with pytest.raises(ConfigurationError, match=env_var):
        create_app()


@pytest.mark.parametrize(
    "env_var",
    [
        "DB_DRIVER",
        "DB_USER",
        "DB_PASS",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
    ],
)
def test_env_db_settings_are_required(
    env_var: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _omit_from_loaded_env(env_var, monkeypatch)
    with pytest.raises(ConfigurationError, match=env_var):
        create_app()
