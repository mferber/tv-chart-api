import pytest
from helpers.testing_data.users import get_user_id
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from models.show import EpisodeDescriptor, EpisodeType, Show, ShowCreate
from services.show import EpisodeNotFound, ShowNotFound, ShowService


@pytest.mark.asyncio
async def test_get_shows(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    result = await sut.get_shows()

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
    assert all_creatures.imdb_id == "tt123"
    assert all_creatures.thetvdb_id == 1234
    assert len(all_creatures.seasons) == 4

    for season_idx, season in enumerate(all_creatures.seasons):
        assert len(season) == 7
        for idx, ep in enumerate(season):
            assert ep.title != "Untitled"
            assert ep.type == ("special" if idx == 6 else "episode")
            assert ep.watched == (True if season_idx == 0 else False)


@pytest.mark.asyncio
async def test_get_show(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows = await sut.get_shows()

    show = await sut.get_show(shows[0].id)

    assert show == shows[0]


@pytest.mark.asyncio
async def test_get_nonexistent_show_fails(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)

    with pytest.raises(ShowNotFound):
        from uuid import uuid4

        await sut.get_show(uuid4())


@pytest.mark.asyncio
async def test_user_get_other_users_show_fails(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id1 = await get_user_id("test_user1", sess)
    user_id2 = await get_user_id("test_user2", sess)
    sut = ShowService(db_session=sess, user_id=user_id1)
    other_user_svc = ShowService(db_session=sess, user_id=user_id2)
    shows = await sut.get_shows()
    show_id = shows[0].id

    with pytest.raises(ShowNotFound):
        await other_user_svc.get_show(show_id)


@pytest.mark.asyncio
async def test_add_show(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    new_show = ShowCreate(
        tvmaze_id=1001,
        title="Fictional Show",
        source="HBO",
        duration=60,
        image_sm_url=HttpUrl("https://images.com/fictional/sm"),
        image_lg_url=HttpUrl("https://images.com/fictional/lg"),
        imdb_id="tt999",
        thetvdb_id=9999,
        seasons=[
            [
                EpisodeDescriptor(title="Season 1 episode", type=EpisodeType.EPISODE, watched=True),
                EpisodeDescriptor(title="Season 1 special", type=EpisodeType.SPECIAL, watched=True),
            ],
            [
                EpisodeDescriptor(title="Season 2 episode", type=EpisodeType.EPISODE, watched=False),
                EpisodeDescriptor(title="Season 2 special", type=EpisodeType.SPECIAL, watched=False),
            ],
        ],
    )
    result = await sut.add_show(new_show)
    assert isinstance(result, Show)

    all_shows = await sut.get_shows()
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
    assert added_show.imdb_id == "tt999"
    assert added_show.thetvdb_id == 9999
    assert len(added_show.seasons) == 2
    assert added_show.seasons[0][0].type == EpisodeType.EPISODE
    assert added_show.seasons[0][1].type == EpisodeType.SPECIAL
    assert added_show.seasons[1][0].type == EpisodeType.EPISODE
    assert added_show.seasons[1][1].type == EpisodeType.SPECIAL
    assert added_show.seasons[0][0].watched
    assert added_show.seasons[0][1].watched
    assert not added_show.seasons[1][0].watched
    assert not added_show.seasons[1][1].watched


@pytest.mark.asyncio
async def test_delete_show(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    id_to_remove = shows_before[0].id

    await sut.delete_show(id_to_remove)

    shows_after = await sut.get_shows()
    assert len(shows_after) == len(shows_before) - 1
    assert id_to_remove not in [show.id for show in shows_after]


@pytest.mark.asyncio
async def test_delete_other_users_show_fails(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id1 = await get_user_id("test_user1", sess)
    user_id2 = await get_user_id("test_user2", sess)
    sut = ShowService(db_session=sess, user_id=user_id1)
    other_user_svc = ShowService(db_session=sess, user_id=user_id2)
    shows_before = await sut.get_shows()
    id_to_remove = shows_before[0].id

    with pytest.raises(ShowNotFound):
        await other_user_svc.delete_show(id_to_remove)
    shows_after = await sut.get_shows()
    assert len(shows_after) == len(shows_before), "delete attempt should have failed"


@pytest.mark.asyncio
async def test_mark_episodes_watched(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    show_to_modify = next(
        filter(lambda show: show.title.startswith("All Creatures"), shows_before)
    )

    # precondition: episodes are unwatched
    assert not (show_to_modify.seasons[1][0].watched)
    assert not (show_to_modify.seasons[1][1].watched)
    assert not (show_to_modify.seasons[1][2].watched)
    assert not (show_to_modify.seasons[1][3].watched)

    await sut.mark_episodes(show_to_modify.id, [(1, 0), (1, 1)], watched=True)

    refetched_show = await sut.get_show(show_to_modify.id)
    assert refetched_show.seasons[1][0].watched
    assert refetched_show.seasons[1][1].watched
    assert not (refetched_show.seasons[1][2].watched)  # other eps unchanged
    assert not (refetched_show.seasons[1][3].watched)


@pytest.mark.asyncio
async def test_mark_nonexistent_episodes_fails(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    show_to_modify = next(
        filter(lambda show: show.title.startswith("All Creatures"), shows_before)
    )

    with pytest.raises(EpisodeNotFound):
        await sut.mark_episodes(show_to_modify.id, [(1000, 2000)], watched=True)
