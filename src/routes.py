from typing import Annotated, Sequence

from litestar import Request, Response, get
from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
from db.models import DbShow
from models.search import SearchResults
from models.show import Show
from services.search.search_service import SearchService


# Health check
@get(path="/health", exclude_from_auth=True)
async def health() -> str:
    return "OK"


# Get active app environment
@get(path="/env", exclude_from_auth=True)
async def env() -> str:
    return app_config.get_app_env()


# "Log out" by deleting current JWT cookie: for some reason, this is not provided
# by litestar-users
@get(path="/auth/logout", exclude_from_auth=True)
async def logout() -> Response[str]:
    response = Response("logout complete")
    response.delete_cookie(key="token")
    return response


# Run a search against TVmaze for shows by title
@get("/search")
async def search(q: str) -> SearchResults:
    result = await SearchService().search(q)
    return result


# List all of the user's saved shows
# FIXME: eventually return domain Show objects, not DbShow; move to service
@get(
    path="/shows",
    return_dto=PydanticDTO[
        Annotated[Show, DTOConfig(exclude={"user_id", "created_at", "updated_at"})]
    ],
)
async def shows(
    request: Request,
    db_session: AsyncSession,
) -> Sequence[Show]:
    current_user_id = request.user.id
    db_shows = (
        await db_session.scalars(
            select(DbShow).where(DbShow.user_id == current_user_id)
        )
    ).all()
    return [db_show.to_show_model() for db_show in db_shows]


all_routes = [health, env, logout, search, shows]
