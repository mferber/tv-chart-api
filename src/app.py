from __future__ import annotations

import logging
from typing import Annotated, Sequence

from advanced_alchemy.base import UUIDBase
from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar, Request, Response, get
from litestar.di import Provide
from litestar.dto import DTOConfig
from litestar.exceptions import NotAuthorizedException
from litestar.status_codes import HTTP_401_UNAUTHORIZED
from litestar_users.dependencies import provide_user_service
from litestar_users.service import BaseUserService
from sqlalchemy import delete, select
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


# health check
@get(path="/health", exclude_from_auth=True)
async def health() -> str:
    return "OK"


# development endpoint to populate minimal database
@get(
    path="/init",
    dependencies={"user_service": Provide(provide_user_service, sync_to_thread=False)},
    exclude_from_auth=True,
)
async def init(
    db_session: AsyncSession, request: Request, user_service: BaseUserService
) -> str:
    from db.models import Show
    from setup.litestar_users.models import User

    await db_session.execute(delete(Show))
    await db_session.execute(delete(User))

    data: dict[str, str] = {"email": "test@example.com", "password": "password"}
    await user_service.register(data, request)

    createdUser: User | None = await db_session.scalar(select(User))
    if createdUser is None:
        raise ValueError("Apparently failed to create user")
    print(repr(createdUser))

    def make_episode(index: int, special: bool, watched: bool) -> dict:
        return {
            "type": "special" if special else "episode",
            "watched": watched,
        }

    pluribus_seasons = [
        {
            "episodes": [make_episode(i, False, i < 8) for i in range(0, 9)],
        }
    ]

    pluribus = Show(
        user_id=createdUser.id,
        tvmaze_id=86175,
        title="Pluribus",
        source="Apple TV",
        duration=60,
        seasons=pluribus_seasons,
    )
    db_session.add(pluribus)

    def all_creatures_season(sn: int) -> dict:
        return {
            "episodes": [
                make_episode(index=i, special=(i == 6), watched=sn <= 2)
                for i in range(0, 7)
            ],
        }

    all_creatures_seasons = [all_creatures_season(s) for s in range(1, 5)]

    all_creatures = Show(
        user_id=createdUser.id,
        tvmaze_id=42836,
        title="All Creatures Great & Small",
        source="PBS",
        duration=60,
        seasons=all_creatures_seasons,
    )
    db_session.add(all_creatures)

    return "Created"


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
    exception_handlers={
        NotAuthorizedException: unauthorized_exception_handler,
    },
    debug=True,
    on_startup=[_on_startup],
    plugins=[
        SQLAlchemyPlugin(config=_sqlAlchemyConfig),
        # litestar-users plugin implements user management and authentication endpoints
        setup.litestar_users.plugin.configure_litestar_users_plugin(
            app_config.JWT_ENCODING_SECRET
        ),
    ],
    route_handlers=[health, search, shows, init],
)
