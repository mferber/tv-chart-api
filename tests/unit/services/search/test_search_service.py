import pytest
import respx
from pydantic import HttpUrl

from services.search import SearchError, SearchService

from .sample_tvmaze_responses.reader import read_sample


@pytest.mark.asyncio
async def test_search_service(respx_mock: respx.MockRouter) -> None:
    text = read_sample("multiple_results.json")
    respx_mock.route(method="GET").respond(text=text)
    svc = SearchService()

    search_results = await svc.search("Battlestar Galactica")

    assert len(search_results.results) == 2

    newBattlestar = search_results.results[0]
    assert newBattlestar.tvmaze_id == 166
    assert newBattlestar.name == "Battlestar Galactica"
    assert newBattlestar.start_year == 2003
    assert newBattlestar.end_year == 2009
    assert newBattlestar.genres == ["Drama", "Science-Fiction", "War"]
    assert newBattlestar.network == "Syfy"
    assert newBattlestar.network_country == "United States"
    assert newBattlestar.streaming_service is None
    assert newBattlestar.streaming_service_country is None
    assert newBattlestar.image_sm_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg"
    )
    assert newBattlestar.image_lg_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/0/2313.jpg"
    )
    assert newBattlestar.summary_html == "<p>Summary 1 truncated</p>"

    oldBattlestar = search_results.results[1]
    assert oldBattlestar.tvmaze_id == 1059
    assert oldBattlestar.name == "Battlestar Galactica"
    assert oldBattlestar.start_year == 1978
    assert oldBattlestar.end_year == 1979
    assert oldBattlestar.genres == ["Action", "Adventure", "Science-Fiction"]
    assert oldBattlestar.network == "ABC"
    assert oldBattlestar.network_country == "United States"
    assert oldBattlestar.streaming_service is None
    assert oldBattlestar.streaming_service_country is None
    assert oldBattlestar.image_sm_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/6/17017.jpg"
    )
    assert oldBattlestar.image_lg_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/6/17017.jpg"
    )
    assert oldBattlestar.summary_html == "<p>Summary 2 truncated</p>"


@pytest.mark.asyncio
async def test_search_service_server_error(respx_mock: respx.MockRouter) -> None:
    respx_mock.route(method="GET").respond(status_code=500)
    with pytest.raises(SearchError):
        svc = SearchService()

        print("GOING")
        _ = await svc.search("Battlestar Galactica")
        print("_")
