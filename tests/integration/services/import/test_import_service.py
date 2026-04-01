import json

import jsonschema
import pytest
from helpers.testing_data.import_data.reader import SampleFileReader
from helpers.testing_data.users import get_user_id
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from services.import_service import ImportService, InvalidImportDataError
from services.show_service import ShowService


@pytest.mark.asyncio
async def test_import_service(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    show_service = ShowService(db_session=sess, user_id=user_id)
    sut = ImportService(show_service=show_service)
    data = SampleFileReader().read("import.json")

    await sut.import_shows(data)

    imported = await show_service.get_shows()

    assert len(imported) == 2

    sherlock_id = next(
        filter(lambda id: imported[id].title == "Sherlock", imported.keys())
    )
    sherlock = imported[sherlock_id]
    battlestar_id = next(
        filter(lambda id: imported[id].title == "Battlestar Galactica", imported.keys())
    )
    battlestar = imported[battlestar_id]

    assert sherlock_id != battlestar_id

    # test Sherlock content
    assert sherlock.tvmaze_id == 335
    assert sherlock.favorite
    assert sherlock.source == "BBC One"
    assert sherlock.duration == 90
    assert sherlock.image_sm_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/171/428042.jpg"
    )
    assert sherlock.image_lg_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/171/428042.jpg"
    )
    assert sherlock.imdb_id == "tt1475582"
    assert sherlock.thetvdb_id == 176941

    # spot-check episodes
    assert sherlock.seasons[0][0].title == "A Study in Pink"
    assert sherlock.seasons[3][3].title == "The Final Problem"
    for seasonIdx, season in enumerate(sherlock.seasons):
        for epIdx, ep in enumerate(season):
            if seasonIdx <= 2:
                assert ep.ep_num == epIdx + 1
            if seasonIdx == 3:
                assert ep.ep_num is None if epIdx == 0 else epIdx
            assert ep.watched if seasonIdx <= 1 else not ep.watched

    # test Battlestar content
    assert battlestar.tvmaze_id == 166
    assert not battlestar.favorite
    assert battlestar.source == "Syfy"
    assert battlestar.duration == 61
    assert battlestar.image_sm_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg"
    )
    assert battlestar.image_lg_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/0/2313.jpg"
    )
    assert battlestar.imdb_id == "tt0407362"
    assert battlestar.thetvdb_id == 73545

    # spot-check episodes
    assert battlestar.seasons[0][0].title == "Battlestar Galactica: The Miniseries (1)"
    assert battlestar.seasons[3][20].title == "Battlestar Galactica: The Plan"
    for seasonIdx, season in enumerate(battlestar.seasons):
        for epIdx, ep in enumerate(season):
            if seasonIdx == 0:
                if epIdx <= 1:  # season 1 starts with 2 specials
                    assert ep.ep_num is None
                else:
                    assert ep.ep_num == epIdx - 1
            else:
                if epIdx >= 20:  # last two seasons end with a special after ep 20
                    assert ep.ep_num is None
                else:
                    assert ep.ep_num == epIdx + 1
            assert ep.watched if seasonIdx <= 2 else not ep.watched


@pytest.mark.asyncio
async def test_import_service_raises_on_malformed_json(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    show_service = ShowService(db_session=sess, user_id=user_id)
    sut = ImportService(show_service=show_service)

    data = '[{ malformed: "data" }]'
    with pytest.raises(InvalidImportDataError) as excinfo:
        await sut.import_shows(data)
    assert isinstance(excinfo.value.__cause__, json.decoder.JSONDecodeError)


@pytest.mark.asyncio
async def test_import_service_raises_on_nonarray_json(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    show_service = ShowService(db_session=sess, user_id=user_id)
    sut = ImportService(show_service=show_service)

    data = '{"not an array": "value"}'
    with pytest.raises(InvalidImportDataError) as excinfo:
        await sut.import_shows(data)
    assert isinstance(excinfo.value.__cause__, jsonschema.exceptions.ValidationError)


@pytest.mark.asyncio
async def test_import_service_raises_on_schema_invalid_data(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user2", sess)
    show_service = ShowService(db_session=sess, user_id=user_id)
    sut = ImportService(show_service=show_service)
    data = SampleFileReader().read("import_schema_invalid.json")

    with pytest.raises(InvalidImportDataError) as excinfo:
        await sut.import_shows(data)
    assert isinstance(excinfo.value.__cause__, jsonschema.exceptions.ValidationError)
