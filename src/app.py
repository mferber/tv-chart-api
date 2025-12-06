from __future__ import annotations

import os

from litestar import Litestar, get

import setup.litestar_users.plugins as litestar_users_plugins
import setup.litestar_users.startup as litestar_users_startup
from exceptions import ConfigurationError
from services.search import SearchResults, SearchService

# --- configuration and initialization ---


def get_db_config() -> dict[str, str]:
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
    return attrs


db_config = get_db_config()
DATABASE_URL = (
    f"{db_config['DEV_DB_DRIVER']}://"
    f"{db_config['DEV_DB_USER']}:{db_config['DEV_DB_PASS']}"
    f"@{db_config['DEV_DB_HOST']}:{db_config['DEV_DB_PORT']}/"
    f"{db_config['DEV_DB_NAME']}"
)

JWT_ENCODING_SECRET = os.getenv("JWT_ENCODING_SECRET")
if JWT_ENCODING_SECRET is None:
    raise ConfigurationError("JWT_ENCODING_SECRET must be set in the environment")


async def on_startup() -> None:
    await litestar_users_startup.on_startup_init_db(DATABASE_URL)


# --- routes ---


@get("/search")
async def search(q: str) -> SearchResults:
    result = await SearchService().search(q)
    return result


# --- app ---


app = Litestar(
    debug=True,
    on_startup=[on_startup],
    plugins=[
        litestar_users_plugins.get_litestar_users_sqlalchemy_init_plugin(DATABASE_URL),
        litestar_users_plugins.configure_litestar_users_plugin(JWT_ENCODING_SECRET),
    ],
    route_handlers=[search],
)
