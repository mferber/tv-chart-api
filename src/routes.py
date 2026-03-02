from uuid import UUID

from litestar import Request, Response, get
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
from models.search import SearchResults
from models.show import Show
from services.search import SearchService
from services.show import ShowService


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
) -> dict[UUID, Show]:
    svc = ShowService(db_session, request.user.id)
    return await svc.get_shows()


# Get a single show from the user's saved shows
@get(path="/shows/{id:uuid}")
async def get_show(request: Request, db_session: AsyncSession, id: UUID) -> Show:
    svc = ShowService(db_session, request.user.id)
    return await svc.get_show(id)


# Add a show to the user's saved shows from TVmaze
@get(path="/add-show")
async def add_show(tvmaze_id: int, request: Request, db_session: AsyncSession) -> Show:
    svc = ShowService(db_session, request.user.id)
    return await svc.add_show_from_tvmaze(tvmaze_id=tvmaze_id)


# FIXME - ?forcerefresh=true or ?skipcache=true to skip cache
# otherwise just fetch from cache if present
# if pulling from TVmaze, always update cache
# NOTE: when part of a user-instigated "refresh show" action, should also refetch show and
# update at least the image URLs, maybe the source or other metadata, if they've changed
# (might as well do the external IDs too)
@get(path="/episodes/{show_id:uuid}")
async def get_episodes(db_session: AsyncSession, show_id: UUID) -> None:
    pass


all_routes = [health, env, logout, search, shows, get_show, add_show, get_episodes]
