from typing import Literal

from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar import (
    AlembicAsyncConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.security.jwt import JWTCookieAuth

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


# Rate limiting: maximum number of requests permitted to a client per minute
RATE_LIMIT_REQ_PER_MIN = 50

# Maximum size of upload (import) file
MAX_FILE_UPLOAD_BYTES = 50_000_000


# --- app ---


def create_app() -> Litestar:
    app_config.load()

    cookie_domain = (
        "couchpotato.robotpie.net" if app_config.get_app_env() == "production" else None
    )

    class MyJWTCookieAuth(JWTCookieAuth):
        domain: str | None = cookie_domain
        secure: bool = True
        samesite: Literal["lax", "strict", "none"] = "lax"

    sqlAlchemyConfig = SQLAlchemyAsyncConfig(
        connection_string=app_config.get_db_url(),
        session_config=AsyncSessionConfig(expire_on_commit=False),
        before_send_handler="autocommit",  # semi-required by litestar-users; good practice anyway
        create_all=False,  # disable automatic table creation
        alembic_config=AlembicAsyncConfig(
            version_table_name="alembic_version",  # default
            script_config="alembic.ini",
            script_location="migrations",
        ),
    )

    cors_config = CORSConfig(
        # FIXME: replace allowed origins with config setting
        allow_origins=["http://localhost:5173", "https://couchpotato.robotpie.net"],
        allow_credentials=True,
    )

    csrf_config = CSRFConfig(
        secret=app_config.get_csrf_secret(),
        header_name=CSRF_HEADER_NAME,
        cookie_name=CSRF_COOKIE_NAME,
        cookie_domain=cookie_domain,
        cookie_secure=True,
        cookie_samesite="lax",
    )

    return Litestar(
        debug=True,
        plugins=[
            SQLAlchemyPlugin(config=sqlAlchemyConfig),
            # litestar-users plugin implements user management and authentication endpoints
            litestar_users_setup.plugin.configure_litestar_users_plugin(
                auth_backend_class=MyJWTCookieAuth,
                jwt_encoding_secret=app_config.get_jwt_encoding_secret(),
            ),
        ],
        cors_config=cors_config,
        csrf_config=csrf_config,
        middleware=[
            RateLimitConfig(rate_limit=("minute", RATE_LIMIT_REQ_PER_MIN)).middleware
        ],
        request_max_body_size=MAX_FILE_UPLOAD_BYTES,
        route_handlers=all_routes,
    )
