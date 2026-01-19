from __future__ import annotations

import logging
import os

from advanced_alchemy.base import UUIDBase
from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar, Request, Response, get
from litestar.exceptions import NotAuthorizedException
from litestar.status_codes import HTTP_401_UNAUTHORIZED

import setup.litestar_users.plugin
from exceptions import ConfigurationError
from services.search import SearchResults, SearchService

"""
Main app: API backend for TV tracker

Defines globals:
- DATABASE_URL: db connection string, constructed from environment variables
- JWT_ENCODING_SECRET: for signing JWTs

"""

# --- configuration and initialization ---


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


# get database url from environment variables
DATABASE_URL = _get_db_url()

# get JWT signing secret from environment variable
JWT_ENCODING_SECRET = os.getenv("JWT_ENCODING_SECRET")
if JWT_ENCODING_SECRET is None:
    raise ConfigurationError("JWT_ENCODING_SECRET must be set in the environment")

# SQLAlchemy config
_sqlAlchemyConfig = SQLAlchemyAsyncConfig(
    connection_string=DATABASE_URL,
    session_config=AsyncSessionConfig(expire_on_commit=False),
    before_send_handler="autocommit",  # semi-required by litestar-users; good practice anyway
)


# Database initialization at startup
async def _on_startup() -> None:
    # FIXME: this should be replaced with proper Alembic use for production (example comes from simple litestar-users example app)

    from db.models import Show  # noqa: F401

    engine = _sqlAlchemyConfig.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)


# --- Log authorization failure details ---
# (temporary: help get visibility into litestar-users)

logger = logging.getLogger(__name__)


def unauthorized_exception_handler(
    request: Request, exc: NotAuthorizedException
) -> Response:
    logger.warning(
        f"Unauthorized request: "
        f"Path={request.url.path}, "
        f"Method={request.method}, "
        f"Headers={dict(request.headers)}, "
        f"Reason={str(exc)}"
    )

    return Response(
        content={"detail": str(exc)},
        status_code=HTTP_401_UNAUTHORIZED,
    )


# --- routes ---


# FIXME: dummy endpoint to test authentication
@get("/hello")
async def hello(request: Request) -> dict[str, str]:
    return {"hello": "world", "you": request.user.email}


# FIXME: move somewhere appropriate when route structure is in place
@get("/search")
async def search(q: str) -> SearchResults:
    result = await SearchService().search(q)
    return result


# --- app ---


app = Litestar(
    exception_handlers={
        NotAuthorizedException: unauthorized_exception_handler,
    },
    debug=True,
    on_startup=[_on_startup],
    plugins=[
        SQLAlchemyPlugin(config=_sqlAlchemyConfig),
        # litestar-users plugin implements user management and authentication endpoints
        setup.litestar_users.plugin.configure_litestar_users_plugin(
            JWT_ENCODING_SECRET
        ),
    ],
    route_handlers=[search, hello],  # FIXME
)
