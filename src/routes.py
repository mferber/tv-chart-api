import datetime
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from litestar import Request, Response, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import HTTP_400_BAD_REQUEST
from sqlalchemy.ext.asyncio import AsyncSession

import app_config
from models.search import SearchResults
from models.show import EpisodeDetails, Show
from services.export_shows import ExportService
from services.import_shows import ImportService, InvalidImportDataError
from services.search import SearchService
from services.show import ShowService


def datetime_filename_suffix() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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


# FIXME: when part of a user-instigated "refresh show" action, should also refetch show and
# update at least the image URLs, maybe the source or other metadata, if they've changed
# (might as well do the external IDs too)
@get(path="/episodes/{show_id:uuid}")
async def get_episodes(
    request: Request,
    db_session: AsyncSession,
    show_id: UUID,
    forcerefresh: bool = False,
) -> list[list[EpisodeDetails]]:
    svc = ShowService(db_session, request.user.id)
    show = await svc.get_show(show_id)
    # FIXME Return 404 if not found
    return await svc.get_episodes(show, force_refresh=True)


@dataclass
class SetWatchedStatusBody:
    show_id: UUID
    episodes: list[tuple[int, int]]  # (season_num, ep_index)


@post(path="/toggle-watched-status")
async def toggle_watched_status(
    data: SetWatchedStatusBody, db_session: AsyncSession, request: Request
) -> Show:
    svc = ShowService(db_session, request.user.id)
    return await svc.toggle_episodes(data.show_id, data.episodes)


@get(
    path="/data/export",
    response_headers={
        "Content-Disposition": f'attachment; filename="couch-potato-backup-{datetime_filename_suffix()}.json"'
    },
)
async def export_data(db_session: AsyncSession, request: Request) -> str:
    svc = ExportService(show_service=ShowService(db_session, request.user.id))
    return await svc.export()


@post(
    path="/data/import",
)
async def import_data(
    data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    db_session: AsyncSession,
    request: Request,
) -> dict | Response:
    raw = await data.read()
    try:
        json_text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return Response(
            {"error": "invalid UTF-8 content", "detail": e.reason},
            status_code=HTTP_400_BAD_REQUEST,
        )

    try:
        svc = ImportService(show_service=ShowService(db_session, request.user.id))
        imported = await svc.import_shows(json_text)
        return {"imported_count": len(imported)}
    except Exception as e:
        if isinstance(e, InvalidImportDataError):
            exc_detail = (
                getattr(e.__cause__, "message", None)
                or getattr(e.__cause__, "msg", None)
                or "none available"
            )
            return Response(
                {"error": "invalid or malformed JSON", "detail": exc_detail},
                status_code=HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {"error": "unknown error"}, status_code=HTTP_400_BAD_REQUEST
            )


all_routes = [
    health,
    env,
    logout,
    search,
    shows,
    get_show,
    add_show,
    get_episodes,
    toggle_watched_status,
    export_data,
    import_data,
]
