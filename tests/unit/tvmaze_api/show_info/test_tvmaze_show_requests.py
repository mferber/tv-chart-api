import pytest
import respx
from pydantic import HttpUrl

from tvmaze_api.client import InvalidResponseError, TVmazeAPIClient
from tvmaze_api.models import TVmazeExternals, TVmazeImage, TVmazeShow
from unit.testing_data.reader import SampleFileReader

sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")


@pytest.mark.asyncio
async def test_show_request(respx_mock: respx.MockRouter) -> None:
    text = sample_file_reader.read("network_show.json")
    route = respx_mock.route(method="GET").respond(text=text)
    client = TVmazeAPIClient()

    rsp = await client.get_show(tvmaze_id=6456)

    # verify TVmaze was called correctly
    assert route.call_count == 1
    url = route.calls.last.request.url
    assert url.path == "/shows/6456"
    assert dict(url.params) == {}

    # verify we deserialized a ShowCreate
    assert isinstance(rsp, TVmazeShow)
    assert rsp.id == 6456
    assert rsp.network and rsp.network.name == "STARZ"
    assert rsp.averageRuntime == 60
    assert rsp.image == TVmazeImage(
        medium=HttpUrl(
            "https://static.tvmaze.com/uploads/images/medium_portrait/175/438213.jpg"
        ),
        original=HttpUrl(
            "https://static.tvmaze.com/uploads/images/original_untouched/175/438213.jpg"
        ),
    )
    assert rsp.externals == TVmazeExternals(imdb="tt4643084", thetvdb=337302)


@pytest.mark.asyncio
async def test_invalid_show_request_fails(respx_mock: respx.MockRouter) -> None:
    text = sample_file_reader.read("network_show_invalid.json")
    respx_mock.route(method="GET").respond(text=text)
    client = TVmazeAPIClient()

    with pytest.raises(InvalidResponseError):
        _ = await client.get_show(tvmaze_id=6456)


@pytest.mark.asyncio
async def test_show_episodes_request(respx_mock: respx.MockRouter) -> None:
    text = sample_file_reader.read("network_show_episodes.json")
    route = respx_mock.route(method="GET").respond(text=text)
    client = TVmazeAPIClient()

    rsp = await client.get_show_episodes(tvmaze_id=6456)

    # verify TVmaze was called correctly
    assert route.call_count == 1
    url = route.calls.last.request.url
    assert url.path == "/shows/6456/episodes"
    assert dict(url.params) == {}

    # verify 2 seasons of 10 episodes
    episodes = rsp.root
    assert len(episodes) == 20
    for ep in episodes:
        assert ep.type == "regular"
    for i in range(0, 10):
        assert episodes[i].season == 1
        assert episodes[i].number == i + 1
    for i in range(11, 20):
        assert episodes[i].season == 2
        assert episodes[i].number == (i + 1) - 10

    # spot check an episode
    episode = episodes[15]
    assert episode.name == "Twin Cities"
    assert episode.airdate == "2019-01-20"
    assert episode.runtime == 60
    assert episode.summary and "The origins of the Crossing" in episode.summary
    print(episode)


@pytest.mark.asyncio
async def test_invalid_show_episodes_request_fails(
    respx_mock: respx.MockRouter,
) -> None:
    text = sample_file_reader.read("network_show_episodes_invalid.json")
    respx_mock.route(method="GET").respond(text=text)
    client = TVmazeAPIClient()

    with pytest.raises(InvalidResponseError):
        _ = await client.get_show_episodes(tvmaze_id=6456)
