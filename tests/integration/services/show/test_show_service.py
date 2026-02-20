from typing import Sequence
from uuid import UUID

import pytest
from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbShow
from models.show import EpisodeDescriptor, EpisodeType, Show, ShowCreate
from services.show import ShowService


@pytest.mark.parametrize("user_id", ["test_user1"], indirect=True)
@pytest.mark.asyncio
async def test_get_shows(autorollback_db_session: AsyncSession, user_id: UUID) -> None:
    sut = ShowService()

    result = await sut.get_shows(autorollback_db_session, user_id)

    assert len(result) == 1
    all_creatures = result[0]
    assert all_creatures.title == "All Creatures Great & Small"
    assert all_creatures.tvmaze_id == 42836
    assert all_creatures.source == "PBS"
    assert all_creatures.duration == 60
    assert all_creatures.image_sm_url == HttpUrl(
        "https://tvimages.com/all_creatures/sm"
    )
    assert all_creatures.image_lg_url == HttpUrl(
        "https://tvimages.com/all_creatures/lg"
    )
    assert len(all_creatures.seasons) == 4

    for season_idx, season in enumerate(all_creatures.seasons):
        assert len(season) == 7
        for idx, ep in enumerate(season):
            assert ep.type == ("special" if idx == 6 else "episode")
            assert ep.watched == (True if season_idx == 0 else False)


@pytest.mark.parametrize("user_id", ["test_user1"], indirect=True)
@pytest.mark.asyncio
async def test_add_show(autorollback_db_session: AsyncSession, user_id: UUID) -> None:
    sut = ShowService()
    new_show = ShowCreate(
        tvmaze_id=1001,
        title="Fictional Show",
        source="HBO",
        duration=60,
        image_sm_url=HttpUrl("https://images.com/fictional/sm"),
        image_lg_url=HttpUrl("https://images.com/fictional/lg"),
        seasons=[
            [
                EpisodeDescriptor(type=EpisodeType.EPISODE, watched=True),
                EpisodeDescriptor(type=EpisodeType.SPECIAL, watched=True),
            ],
            [
                EpisodeDescriptor(type=EpisodeType.EPISODE, watched=False),
                EpisodeDescriptor(type=EpisodeType.SPECIAL, watched=False),
            ],
        ],
    )
    result = await sut.add_show(new_show, autorollback_db_session, user_id)
    assert isinstance(result, Show)

    all_shows = await ShowService().get_shows(autorollback_db_session, user_id)
    assert len(all_shows) == 2
    added_show = next(filter(lambda show: show.id == result.id, all_shows))
    assert added_show is not None
    assert added_show == result

    assert not hasattr(added_show, "user_id")
    assert added_show.tvmaze_id == 1001
    assert added_show.title == "Fictional Show"
    assert added_show.source == "HBO"
    assert added_show.duration == 60
    assert added_show.image_sm_url == HttpUrl("https://images.com/fictional/sm")
    assert added_show.image_lg_url == HttpUrl("https://images.com/fictional/lg")
    assert len(added_show.seasons) == 2
    assert added_show.seasons[0][0].type == EpisodeType.EPISODE
    assert added_show.seasons[0][1].type == EpisodeType.SPECIAL
    assert added_show.seasons[1][0].type == EpisodeType.EPISODE
    assert added_show.seasons[1][1].type == EpisodeType.SPECIAL
    assert added_show.seasons[0][0].watched
    assert added_show.seasons[0][1].watched
    assert not added_show.seasons[1][0].watched
    assert not added_show.seasons[1][1].watched


@pytest.mark.parametrize("user_id", ["test_user1"], indirect=True)
@pytest.mark.asyncio
async def test_delete_show(
    autorollback_db_session: AsyncSession, user_id: UUID
) -> None:
    sess = autorollback_db_session

    async def get_all_show_uuids() -> Sequence[UUID]:
        query = select(DbShow.id).where(DbShow.user_id == user_id)
        return (await sess.scalars(query)).all()

    uuids_before = await get_all_show_uuids()
    uuid_to_remove = uuids_before[0]

    sut = ShowService()
    await sut.delete_show(uuid_to_remove, sess, user_id)

    uuids_after = await get_all_show_uuids()
    assert len(uuids_after) == len(uuids_before) - 1
    assert uuid_to_remove not in uuids_after
