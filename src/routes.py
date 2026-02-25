import asyncio
from typing import Sequence
from uuid import UUID

from litestar import Request, Response, get
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
from db.models import DbShow
from models.search import SearchResults
from models.show import Show
from services.search import SearchService
from services.show import ShowService
from tvmaze_api.client import TVmazeAPIClient


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
    client = TVmazeAPIClient()

    # fetch show and episode metadata
    rsp, rsp2 = await asyncio.gather(
        client.get_show(tvmaze_id=tvmaze_id),
        client.get_show_episodes(tvmaze_id=tvmaze_id),
    )

    # insert new show in db
    addable = rsp.to_show_create_model(with_episodes=rsp2)
    dbmodel = DbShow.from_show_model(addable, owner_id=request.user.id)
    db_session.add(dbmodel)
    await db_session.flush()

    # return the newly added show to the caller, including its assigned id
    show = dbmodel.to_show_model()
    return show


all_routes = [health, env, logout, search, shows, get_show, add_show]
