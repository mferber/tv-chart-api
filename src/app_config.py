"""
Defines:
- DATABASE_URL: db connection string, constructed from environment variables
- JWT_ENCODING_SECRET: for signing JWTs
"""

import os

from dotenv import load_dotenv

from exceptions import ConfigurationError

load_dotenv()


def _get_app_env() -> str:
    """Read app environment from environment vars"""
    return os.getenv("APP_ENV") or "production"


def _get_db_url() -> str:
    """Construct DB url from environment vars"""
    attrs = {}
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


def _get_jwt_encoding_secret() -> str:
    secret = os.getenv("JWT_ENCODING_SECRET")
    if secret is None:
        raise ConfigurationError("JWT_ENCODING_SECRET must be set in the environment")
    return secret


# Set exported variables
APP_ENV = _get_app_env()
DATABASE_URL = _get_db_url()
JWT_ENCODING_SECRET = _get_jwt_encoding_secret()
