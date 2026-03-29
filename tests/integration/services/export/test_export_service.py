import json
from typing import Any

import pytest
from helpers.testing_data.users import get_user_id
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from models.show import Show
from services.export_shows import ExportService
from services.import_shows import ImportService
from services.show import ShowService


@pytest.mark.asyncio
async def test_export_service(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    show_service = ShowService(db_session=sess, user_id=user_id)
    sut = ExportService(show_service=show_service)

    export = await sut.export()

    exported_shows = json.loads(export)

    # validate the export as if we were importing it
    ImportService.schema_validate_import_data(exported_shows)

    # check all fields against the source Show objects
    orig_shows = await show_service.get_shows()

    assert len(exported_shows) == 2

    exported_pluribus: dict[str, Any] = next(
        filter(lambda show: show["title"] == "Pluribus", exported_shows)
    )
    pluribus: Show = next(
        filter(lambda show: show.title == "Pluribus", orig_shows.values())
    )
    exported_severance = next(
        filter(lambda show: show["title"] == "Severance", exported_shows)
    )
    severance: Show = next(
        filter(lambda show: show.title == "Severance", orig_shows.values())
    )

    for exported_show, original_show in [
        (exported_pluribus, pluribus),
        (exported_severance, severance),
    ]:
        assert exported_show["title"] == original_show.title
        assert exported_show["favorite"] == original_show.favorite
        assert exported_show["tvmaze_id"] == original_show.tvmaze_id
        assert exported_show["source"] == original_show.source
        assert exported_show["duration"] == original_show.duration
        assert HttpUrl(exported_show["image_sm_url"]) == original_show.image_sm_url
        assert HttpUrl(exported_show["image_lg_url"]) == original_show.image_lg_url
        assert exported_show["imdb_id"] == original_show.imdb_id
        assert exported_show["thetvdb_id"] == original_show.thetvdb_id

        assert len(exported_show["seasons"]) == len(original_show.seasons)

        for s_idx, season in enumerate(exported_show["seasons"]):
            assert len(season) == len(original_show.seasons[s_idx])

            for ep_idx, exported_episode in enumerate(season):
                episode = original_show.seasons[s_idx][ep_idx]
                assert exported_episode["title"] == episode.title
                assert exported_episode["ep_num"] == episode.ep_num
                assert exported_episode["watched"] == episode.watched
