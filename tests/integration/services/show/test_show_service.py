import datetime
from uuid import uuid4

import pytest
import respx
from helpers.testing_data.mock_responses.reader import SampleFileReader
from helpers.testing_data.users import get_user_id
from pydantic import HttpUrl
from pytest_mock import MockerFixture
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
    all_creatures = next(iter(result.values()))
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
            assert ep.ep_num == (idx + 1 if idx < 6 else None)
            assert ep.watched == (True if season_idx == 0 else False)


@pytest.mark.asyncio
async def test_get_show(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows = await sut.get_shows()
    selected_show = next(iter(shows.values()))

    show = await sut.get_show(selected_show.id)

    assert show == selected_show


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
    show_id = next(iter(shows.values())).id

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
        favorite=True,
        source="HBO",
        duration=60,
        image_sm_url=HttpUrl("https://images.com/fictional/sm"),
        image_lg_url=HttpUrl("https://images.com/fictional/lg"),
        imdb_id="tt999",
        thetvdb_id=9999,
        seasons=[
            [
                EpisodeDescriptor(
                    title="Season 1 episode",
                    ep_num=1,
                    watched=True,
                ),
                EpisodeDescriptor(
                    title="Season 1 special",
                    ep_num=None,
                    watched=True,
                ),
            ],
            [
                EpisodeDescriptor(
                    title="Season 2 episode",
                    ep_num=1,
                    watched=False,
                ),
                EpisodeDescriptor(
                    title="Season 2 special",
                    ep_num=None,
                    watched=False,
                ),
            ],
        ],
    )
    result = await sut.add_show(new_show)
    assert isinstance(result, Show)

    all_shows = await sut.get_shows()
    assert len(all_shows) == 2
    added_show = all_shows[result.id]
    assert added_show is not None
    assert added_show == result

    assert not hasattr(added_show, "user_id")
    assert added_show.tvmaze_id == 1001
    assert added_show.title == "Fictional Show"
    assert added_show.favorite
    assert added_show.source == "HBO"
    assert added_show.duration == 60
    assert added_show.image_sm_url == HttpUrl("https://images.com/fictional/sm")
    assert added_show.image_lg_url == HttpUrl("https://images.com/fictional/lg")
    assert added_show.imdb_id == "tt999"
    assert added_show.thetvdb_id == 9999
    assert len(added_show.seasons) == 2
    assert len(added_show.seasons[0]) == 2
    assert len(added_show.seasons[1]) == 2
    assert added_show.seasons[0][0].ep_num is not None
    assert added_show.seasons[0][1].ep_num is None
    assert added_show.seasons[1][0].ep_num is not None
    assert added_show.seasons[1][1].ep_num is None
    assert added_show.seasons[0][0].watched
    assert added_show.seasons[0][1].watched
    assert not added_show.seasons[1][0].watched
    assert not added_show.seasons[1][1].watched


@pytest.mark.asyncio
async def test_add_many_shows(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    new_show1 = ShowCreate(
        tvmaze_id=1001,
        title="Fictional Show 1",
        favorite=True,
        source="Source1",
        duration=1,
        image_sm_url=HttpUrl("https://images.com/fictional1/sm"),
        image_lg_url=HttpUrl("https://images.com/fictional1/lg"),
        imdb_id="tt1",
        thetvdb_id=1,
        seasons=[
            [
                EpisodeDescriptor(
                    title="Show 1 Season 1 Episode 1",
                    ep_num=1,
                    watched=False,
                ),
            ],
        ],
    )
    new_show2 = ShowCreate(
        tvmaze_id=1002,
        title="Fictional Show 2",
        favorite=False,
        source="Source2",
        duration=2,
        image_sm_url=HttpUrl("https://images.com/fictional2/sm"),
        image_lg_url=HttpUrl("https://images.com/fictional2/lg"),
        imdb_id="tt2",
        thetvdb_id=2,
        seasons=[
            [
                EpisodeDescriptor(
                    title="Show 2 Season 1 Episode 1",
                    ep_num=1,
                    watched=True,
                ),
            ],
        ],
    )

    # to make sure another user's shows aren't affected
    other_user_id = await get_user_id("test_user2", sess)
    other_user_service = ShowService(db_session=sess, user_id=other_user_id)
    other_user_show_count_before = len(await other_user_service.get_shows())
    assert other_user_show_count_before != 0

    results = await sut.add_many_shows([new_show1, new_show2])

    assert isinstance(results, list)
    assert isinstance(results[0], Show)
    assert isinstance(results[1], Show)

    all_shows = await sut.get_shows()
    assert len(all_shows) == 3
    added_show1 = all_shows[results[0].id]
    assert added_show1 is not None
    assert added_show1 in results
    added_show2 = all_shows[results[1].id]
    assert added_show2 is not None
    assert added_show2 in results

    assert not hasattr(added_show1, "user_id")
    assert added_show1.tvmaze_id == 1001
    assert added_show1.title == "Fictional Show 1"
    assert added_show1.source == "Source1"
    assert added_show1.duration == 1
    assert added_show1.image_sm_url == HttpUrl("https://images.com/fictional1/sm")
    assert added_show1.image_lg_url == HttpUrl("https://images.com/fictional1/lg")
    assert added_show1.imdb_id == "tt1"
    assert added_show1.thetvdb_id == 1
    assert len(added_show1.seasons) == 1
    assert len(added_show1.seasons[0]) == 1
    assert added_show1.seasons[0][0].title == "Show 1 Season 1 Episode 1"
    assert added_show1.seasons[0][0].ep_num is not None
    assert not added_show1.seasons[0][0].watched

    assert not hasattr(added_show2, "user_id")
    assert added_show2.tvmaze_id == 1002
    assert added_show2.title == "Fictional Show 2"
    assert added_show2.source == "Source2"
    assert added_show2.duration == 2
    assert added_show2.image_sm_url == HttpUrl("https://images.com/fictional2/sm")
    assert added_show2.image_lg_url == HttpUrl("https://images.com/fictional2/lg")
    assert added_show2.imdb_id == "tt2"
    assert added_show2.thetvdb_id == 2
    assert len(added_show2.seasons) == 1
    assert len(added_show2.seasons[0]) == 1
    assert added_show2.seasons[0][0].title == "Show 2 Season 1 Episode 1"
    assert added_show2.seasons[0][0].ep_num is not None
    assert added_show2.seasons[0][0].watched

    other_user_show_count_after = len(await other_user_service.get_shows())
    assert other_user_show_count_after == other_user_show_count_before


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_add_show_from_tvmaze_adds_show_to_db(
    autorollback_db_session: AsyncSession, respx_mock: respx.MockRouter
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)

    # this test uses TVmazeClient: mock out TVmaze URLs
    sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")
    show_json = sample_file_reader.read("network_show.json")
    respx_mock.get("https://api.tvmaze.com/shows/6456").respond(text=show_json)
    episodes_json = sample_file_reader.read("network_show_episodes.json")
    respx_mock.get("https://api.tvmaze.com/shows/6456/episodes").respond(
        text=episodes_json
    )

    # precondition
    shows_before = await sut.get_shows()
    assert len(shows_before) == 1

    # run test
    result = await sut.add_show_from_tvmaze(tvmaze_id=6456)

    shows_after = await sut.get_shows()
    assert len(shows_after) == 2
    added_show = shows_after[result.id]
    assert added_show is not None
    assert added_show == result

    assert not hasattr(added_show, "user_id")
    assert added_show.tvmaze_id == 6456
    assert added_show.title == "Counterpart"
    assert added_show.source == "STARZ"
    assert added_show.duration == 60
    assert added_show.imdb_id == "tt4643084"
    assert len(added_show.seasons) == 2
    assert len(added_show.seasons[0]) == 10
    assert len(added_show.seasons[1]) == 10


@pytest.mark.asyncio
async def test_add_show_caches_episode_list(
    autorollback_db_session: AsyncSession, respx_mock: respx.MockRouter
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)

    ShowService.episodes_cache.clear()

    # this test uses TVmazeClient: mock out TVmaze URLs
    sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")
    show_json = sample_file_reader.read("network_show.json")
    respx_mock.get("https://api.tvmaze.com/shows/6456").respond(text=show_json)
    episodes_json = sample_file_reader.read("network_show_episodes.json")
    respx_mock.get("https://api.tvmaze.com/shows/6456/episodes").respond(
        text=episodes_json
    )

    # preconditions
    shows_before = await sut.get_shows()
    assert len(shows_before) == 1

    # run test
    added = await sut.add_show_from_tvmaze(tvmaze_id=6456)

    assert ShowService.episodes_cache.currsize == 1
    cached = ShowService.episodes_cache[added.id]
    assert cached is not None
    assert len(cached) == 2
    for season_idx in range(0, 1):
        assert len(cached[season_idx]) == 10


@pytest.mark.asyncio
async def test_delete_show(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    id_to_remove = next(iter(shows_before.values())).id

    await sut.delete_show(id_to_remove)

    shows_after = await sut.get_shows()
    assert len(shows_after) == len(shows_before) - 1
    assert id_to_remove not in [show.id for show in shows_after.values()]


@pytest.mark.asyncio
async def test_delete_all_shows(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    assert len(shows_before) != 0  # precondition

    # to make sure another user's shows aren't affected
    other_user_id = await get_user_id("test_user2", sess)
    other_user_service = ShowService(db_session=sess, user_id=other_user_id)
    other_user_show_count_before = len(await other_user_service.get_shows())
    assert other_user_show_count_before != 0

    await sut.delete_all_shows()

    shows_after = await sut.get_shows()
    assert len(shows_after) == 0

    other_user_show_count_after = len(await other_user_service.get_shows())
    assert other_user_show_count_after == other_user_show_count_before


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_episodes_uncached(
    autorollback_db_session: AsyncSession, respx_mock: respx.MockRouter
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    show = Show(
        id=uuid4(),
        tvmaze_id=1,
        title="Fictional Show",
        favorite=True,
        source="Somewhere",
        duration=30,
        image_lg_url=None,
        image_sm_url=None,
        imdb_id=None,
        thetvdb_id=None,
        seasons=[],
    )
    ShowService.episodes_cache.clear()

    # fake TVmaze response
    sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")
    show_json = sample_file_reader.read("network_show_episodes.json")
    respx_mock.route(method="GET").respond(text=show_json)

    episodes = await sut.get_episodes(show)

    assert len(episodes) > 0
    # FIXME: more assertions

    assert len(ShowService.episodes_cache) == 1


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_episodes_cached(
    autorollback_db_session: AsyncSession,
    respx_mock: respx.MockRouter,
    mocker: MockerFixture,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    show = Show(
        id=uuid4(),
        tvmaze_id=1,
        title="Fictional Show",
        favorite=True,
        source="Somewhere",
        duration=30,
        image_lg_url=None,
        image_sm_url=None,
        imdb_id=None,
        thetvdb_id=None,
        seasons=[],
    )

    ShowService.episodes_cache.clear()
    cache_spy = mocker.spy(ShowService.episodes_cache, "get")

    # fake TVmaze response
    sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")
    show_json = sample_file_reader.read("network_show_episodes.json")
    route = respx_mock.route(method="GET").respond(text=show_json)

    episodes1 = await sut.get_episodes(show)
    episodes2 = await sut.get_episodes(show)

    assert len(episodes1) > 0
    assert len(episodes1) == len(episodes2)

    # because of cache, only the first request should attempt to query TVmaze
    assert route.call_count == 1
    assert cache_spy.call_count == 2  # cache was checked twice

    assert episodes2[0][0].title == "The Crossing"
    assert episodes2[0][0].summary and "Howard Silk" in episodes2[0][0].summary
    assert episodes2[0][0].type == EpisodeType.EPISODE
    assert episodes2[0][0].duration == 60
    assert episodes2[0][0].release_date == datetime.date(2017, 12, 10)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_episodes_cached_with_force_refresh(
    autorollback_db_session: AsyncSession,
    respx_mock: respx.MockRouter,
    mocker: MockerFixture,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    show = Show(
        id=uuid4(),
        tvmaze_id=1,
        title="Fictional Show",
        favorite=True,
        source="Somewhere",
        duration=30,
        image_lg_url=None,
        image_sm_url=None,
        imdb_id=None,
        thetvdb_id=None,
        seasons=[],
    )

    ShowService.episodes_cache.clear()
    cache_spy = mocker.spy(ShowService.episodes_cache, "get")

    # fake TVmaze response
    sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")
    show_json = sample_file_reader.read("network_show_episodes.json")
    route = respx_mock.route(method="GET").respond(text=show_json)

    # run test
    episodes1 = await sut.get_episodes(show)  # caches results
    episodes2 = await sut.get_episodes(show, force_refresh=True)

    assert len(episodes1) > 0
    assert len(episodes1) == len(episodes2)

    # because of force refresh, we should skip cache and run the tvmaze query twice
    assert route.call_count == 2
    assert cache_spy.call_count == 1  # cache was checked for first call only

    assert episodes2[0][0].title == "The Crossing"
    assert episodes2[0][0].summary and "Howard Silk" in episodes2[0][0].summary
    assert episodes2[0][0].type == EpisodeType.EPISODE
    assert episodes2[0][0].duration == 60
    assert episodes2[0][0].release_date == datetime.date(2017, 12, 10)


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
    id_to_remove = next(iter(shows_before.values())).id

    with pytest.raises(ShowNotFound):
        await other_user_svc.delete_show(id_to_remove)
    shows_after = await sut.get_shows()
    assert len(shows_after) == len(shows_before), "delete attempt should have failed"


@pytest.mark.asyncio
async def test_toggle_episodes_watched(autorollback_db_session: AsyncSession) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    show_to_modify = next(
        filter(
            lambda show: show.title.startswith("All Creatures"), shows_before.values()
        )
    )

    # precondition
    assert show_to_modify.seasons[0][0].watched
    assert show_to_modify.seasons[0][1].watched
    assert not (show_to_modify.seasons[1][0].watched)
    assert not (show_to_modify.seasons[1][1].watched)

    assert not (show_to_modify.seasons[2][0].watched)
    assert not (show_to_modify.seasons[2][1].watched)

    await sut.toggle_episodes(show_to_modify.id, [(0, 0), (0, 1), (1, 0), (1, 1)])

    refetched_show = await sut.get_show(show_to_modify.id)
    assert not (refetched_show.seasons[0][0].watched)
    assert not (refetched_show.seasons[0][1].watched)
    assert refetched_show.seasons[1][0].watched
    assert refetched_show.seasons[1][1].watched

    # unlisted episodes should not change
    assert not (show_to_modify.seasons[2][0].watched)
    assert not (show_to_modify.seasons[2][1].watched)


@pytest.mark.asyncio
async def test_toggle_nonexistent_episodes_fails(
    autorollback_db_session: AsyncSession,
) -> None:
    sess = autorollback_db_session
    user_id = await get_user_id("test_user1", sess)
    sut = ShowService(db_session=sess, user_id=user_id)
    shows_before = await sut.get_shows()
    show_to_modify = next(
        filter(
            lambda show: show.title.startswith("All Creatures"), shows_before.values()
        )
    )

    with pytest.raises(EpisodeNotFound):
        await sut.toggle_episodes(show_to_modify.id, [(1000, 2000)])
