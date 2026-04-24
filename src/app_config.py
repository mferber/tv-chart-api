"""
Defines:
- APP_ENV: string designating the current backend environment; fetchable via /env
- DATABASE_URL: db connection string, constructed from environment variables
- JWT_ENCODING_SECRET: for signing JWTs
"""

import os

from dotenv import dotenv_values, load_dotenv

from exceptions import ConfigurationError

_loaded = False


# Tests that manipulate env settings should monkeypatch this with a no-op if they
# have already called load_dotenv
def load() -> None:
    global _loaded

    if not _loaded:
        values = dotenv_values()
        if values is None:
            print("LOADING ENVIRONMENT VARIABLES: none found")
        else:
            print("LOADING ENVIRONMENT VARIABLES:")
            for k in sorted(values):
                val = values[k]
                if "secret" in k.casefold():
                    val = "**SECRET**"
                print(f"  {k}: {repr(val)}")
        load_dotenv()
    _loaded = True


# Tests that manipulate env settings should monkeypatch this with a no-op if they
# have already called load_dotenv
def check_loaded() -> None:
    if not _loaded:
        raise ConfigurationError("Tried to get configuration settings before loading")


def get_app_env() -> str:
    """Read app environment from environment vars"""
    check_loaded()
    return os.getenv("APP_ENV") or "production"


def get_db_url() -> str:
    """Construct DB url from environment vars"""
    check_loaded()

    if full_url := os.getenv("DATABASE_URL"):
        return full_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise ConfigurationError(
        "Database configuration must be set in the environment: DATABASE_URL is missing"
    )


def get_jwt_encoding_secret() -> str:
    check_loaded()
    secret = os.getenv("JWT_ENCODING_SECRET")
    if secret is None:
        raise ConfigurationError("JWT_ENCODING_SECRET must be set in the environment")
    return secret


def get_csrf_secret() -> str:
    check_loaded()
    secret = os.getenv("CSRF_SECRET")
    if secret is None:
        raise ConfigurationError("CSRF_SECRET must be set in the environment")
    return secret
