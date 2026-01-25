from __future__ import annotations

from typing import Annotated, Sequence

from advanced_alchemy.base import UUIDBase
from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar, get
from litestar.config.csrf import CSRFConfig
from litestar.dto import DTOConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
import setup.litestar_users.plugin
from db.models import Show
from services.search import SearchResults, SearchService

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


# --- routes ---


# Health check
@get(path="/health", exclude_from_auth=True)
async def health() -> str:
    return "OK"


# Get active app environment
@get(path="/env", exclude_from_auth=True)
async def env() -> str:
    return app_config.APP_ENV


# FIXME: move somewhere appropriate when route structure is in place
@get("/search")
async def search(q: str) -> SearchResults:
    result = await SearchService().search(q)
    return result


# FIXME move to service; move endpoint somewhere
@get(
    path="/shows",
    return_dto=SQLAlchemyDTO[
        Annotated[Show, DTOConfig(exclude={"user_id", "created_at", "updated_at"})]
    ],
)
async def shows(
    db_session: AsyncSession,
) -> Sequence[Show]:
    return (await db_session.scalars(select(Show))).all()


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
    csrf_config=CSRFConfig(secret=app_config.CSRF_SECRET),
    route_handlers=[health, env, search, shows],
)
