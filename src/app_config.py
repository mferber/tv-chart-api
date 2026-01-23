"""
Defines:
- DATABASE_URL: db connection string, constructed from environment variables
- JWT_ENCODING_SECRET: for signing JWTs
"""

import os

from exceptions import ConfigurationError


def _get_app_env() -> str:
    """Read app environment from environment vars"""
    return os.getenv("APP_ENV") or "production"


def _get_db_url() -> str:
    """Construct DB url from environment vars"""
    attrs = {}
    for env_name in [
        "DEV_DB_DRIVER",
        "DEV_DB_USER",
        "DEV_DB_PASS",
        "DEV_DB_HOST",
        "DEV_DB_PORT",
        "DEV_DB_NAME",
    ]:
        value = os.getenv(env_name)
        if value is None:
            raise ConfigurationError(
                f"Database configuration must be fully set in the environment ({env_name} is missing)"
            )
        attrs[env_name] = value
    return (
        f"{attrs['DEV_DB_DRIVER']}://"
        f"{attrs['DEV_DB_USER']}:{attrs['DEV_DB_PASS']}"
        f"@{attrs['DEV_DB_HOST']}:{attrs['DEV_DB_PORT']}/"
        f"{attrs['DEV_DB_NAME']}"
    )


def _get_jwt_encoding_secret() -> str:
    secret = os.getenv("JWT_ENCODING_SECRET")
    if secret is None:
        raise ConfigurationError("JWT_ENCODING_SECRET must be set in the environment")
    return secret


# Set exported variables
APP_ENV = _get_app_env()
DATABASE_URL = _get_db_url()
JWT_ENCODING_SECRET = _get_jwt_encoding_secret()
