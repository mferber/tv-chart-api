"""
Defines:
- DATABASE_URL: db connection string, constructed from environment variables
- JWT_ENCODING_SECRET: for signing JWTs
"""

import os

from dotenv import load_dotenv

from exceptions import ConfigurationError

# tests may monkeypatch this to True to suppress loading environment settings, if
# they call load() themselves (e.g. when testing behavior with missing env vars)
_loaded = False


def load() -> None:
    global _loaded

    if (not _loaded):
        load_dotenv()
    _loaded = True


def _check_loaded() -> None:
    if not _loaded:
        raise ConfigurationError("Tried to get configuration settings before loading")


def get_app_env() -> str:
    """Read app environment from environment vars"""
    _check_loaded()
    return os.getenv("APP_ENV") or "production"


def get_db_url() -> str:
    """Construct DB url from environment vars"""
    _check_loaded()
    attrs: dict[str, str] = {}
    for env_name in [
        "DB_DRIVER",
        "DB_USER",
        "DB_PASS",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
    ]:
        value = os.getenv(env_name)
        if value is None:
            raise ConfigurationError(
                f"Database configuration must be fully set in the environment ({env_name} is missing)"
            )
        attrs[env_name] = value
    return (
        f"{attrs['DB_DRIVER']}://"
        f"{attrs['DB_USER']}:{attrs['DB_PASS']}"
        f"@{attrs['DB_HOST']}:{attrs['DB_PORT']}/"
        f"{attrs['DB_NAME']}"
    )


def get_jwt_encoding_secret() -> str:
    _check_loaded()
    secret = os.getenv("JWT_ENCODING_SECRET")
    if secret is None:
        raise ConfigurationError("JWT_ENCODING_SECRET must be set in the environment")
    return secret


def get_csrf_secret() -> str:
    _check_loaded()
    secret = os.getenv("CSRF_SECRET")
    if secret is None:
        raise ConfigurationError("CSRF_SECRET must be set in the environment")
    return secret
