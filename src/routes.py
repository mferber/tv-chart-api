from typing import Annotated, Sequence

from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO
from litestar import Response, get
from litestar.dto import DTOConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
from db.models import Show
from services.search import SearchResults, SearchService


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
