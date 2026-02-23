from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar
from litestar.config.csrf import CSRFConfig

import app_config
import litestar_users_setup.plugin
from routes import all_routes

"""
Main app: API backend for TV tracker
"""

# --- configuration and initialization ---

# These are the defaults, but making it explicit for ease of reference
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "X-CSRFToken"


# --- app ---


def create_app() -> Litestar:
    app_config.load()

    return Litestar(
        debug=True,
        plugins=[
            SQLAlchemyPlugin(
                config=SQLAlchemyAsyncConfig(
                    connection_string=app_config.get_db_url(),
                    session_config=AsyncSessionConfig(expire_on_commit=False),
                    before_send_handler="autocommit",  # semi-required by litestar-users; good practice anyway
                )
            ),
            # litestar-users plugin implements user management and authentication endpoints
            litestar_users_setup.plugin.configure_litestar_users_plugin(
                app_config.get_jwt_encoding_secret()
            ),
        ],
        csrf_config=CSRFConfig(
            secret=app_config.get_csrf_secret(),
            cookie_name=CSRF_COOKIE_NAME,
            header_name=CSRF_HEADER_NAME,
        ),
        route_handlers=all_routes,
    )
