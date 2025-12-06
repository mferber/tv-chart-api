from __future__ import annotations

import os

from litestar import Litestar, get

import setup.litestar_users.plugins as litestar_users_plugins
import setup.litestar_users.startup as litestar_users_startup
from exceptions import ConfigurationError
from services.search import SearchResults, SearchService

# --- configuration and initialization ---

DATABASE_URL = (
    f"{os.getenv('DEV_DB_DRIVER')}://"
    f"{os.getenv('DEV_DB_USER')}:{os.getenv('DEV_DB_PASS')}"
    f"@{os.getenv('DEV_DB_HOST')}:{os.getenv('DEV_DB_PORT')}/"
    f"{os.getenv('DEV_DB_NAME')}"
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
