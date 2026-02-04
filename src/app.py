from __future__ import annotations

from advanced_alchemy.base import UUIDBase
from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar
from litestar.config.csrf import CSRFConfig

import app_config
import setup.litestar_users.plugin
from routes import env, health, logout, search, shows

"""
Main app: API backend for TV tracker
"""

# --- configuration and initialization ---

# SQLAlchemy config
_sqlAlchemyConfig = SQLAlchemyAsyncConfig(
    connection_string=app_config.DATABASE_URL,
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


# --- app ---

app = Litestar(
    debug=True,
    on_startup=[_on_startup],
    plugins=[
        SQLAlchemyPlugin(config=_sqlAlchemyConfig),
        # litestar-users plugin implements user management and authentication endpoints
        setup.litestar_users.plugin.configure_litestar_users_plugin(
            app_config.JWT_ENCODING_SECRET
        ),
    ],
    csrf_config=CSRFConfig(
        secret=app_config.CSRF_SECRET,
        cookie_name="csrftoken",  # default, but make it explicit for ease of reference
        header_name="x-csrftoken",  # ditto
    ),
    route_handlers=[health, env, logout, search, shows],
)
