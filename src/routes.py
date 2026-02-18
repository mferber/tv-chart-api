from typing import Sequence

from litestar import Request, Response, get, post
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
from models.search import SearchResults
from models.show import Show, ShowCreate
from services.search.search_service import SearchService
from services.show_service import ShowService


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
@get(path="/shows")
async def shows(
    request: Request,
    db_session: AsyncSession,
) -> Sequence[Show]:
    return await ShowService().get_shows(db_session, request.user.id)


# Add a show to the user's saved shows
@post(path="/shows")
async def add_show(
    data: ShowCreate, request: Request, db_session: AsyncSession
) -> Show:
    return await ShowService().add_show(data, db_session, request.user.id)


all_routes = [health, env, logout, search, shows, add_show]
