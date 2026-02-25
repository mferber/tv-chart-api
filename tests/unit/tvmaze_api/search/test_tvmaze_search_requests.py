import datetime

import pytest
import respx
from helpers.testing_data.mock_responses.reader import SampleFileReader
from pydantic import HttpUrl

from tvmaze_api.client import InvalidResponseError, TVmazeAPIClient
from tvmaze_api.models import (
    TVmazeCountry,
    TVmazeImage,
    TVmazeNetwork,
    TVmazeSearchResult,
    TVmazeSearchResultShow,
)

sample_file_reader = SampleFileReader("sample_tvmaze_search_results")


@pytest.mark.asyncio
async def test_search_request(respx_mock: respx.MockRouter) -> None:
    text = sample_file_reader.read("multiple_results.json")
    route = respx_mock.route(method="GET").respond(text=text)
    client = TVmazeAPIClient()

    rsp = await client.search_shows("query")

    # verify TVmaze was called correctly
    assert route.call_count == 1
    url = route.calls.last.request.url
    assert url.path == "/search/shows"
    assert dict(url.params) == {"q": "query"}

    # verify we extracted the expected pydantic model
    expected = pydantic_model_battlestar_galactica_results()
    assert rsp.root == expected


@pytest.mark.asyncio
async def test_invalid_response_raises(respx_mock: respx.MockRouter) -> None:
    text = sample_file_reader.read("multiple_results_invalid.json")
    route = respx_mock.route(method="GET").respond(text=text)

    with pytest.raises(InvalidResponseError):
        client = TVmazeAPIClient()

        try:
            await client.search_shows("query")
        except InvalidResponseError:
            assert route.call_count == 1
            raise


# --- Helpers ---


def pydantic_model_battlestar_galactica_results() -> list[TVmazeSearchResult]:
    return [
        TVmazeSearchResult(
            show=TVmazeSearchResultShow(
                id=166,
                name="Battlestar Galactica",
                genres=["Drama", "Science-Fiction", "War"],
                premiered=datetime.date(2003, 12, 8),
                ended=datetime.date(2009, 10, 27),
                network=TVmazeNetwork(
                    name="Syfy", country=TVmazeCountry(name="United States")
                ),
                webChannel=None,
                image=TVmazeImage(
                    medium=HttpUrl(
                        "https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg"
                    ),
                    original=HttpUrl(
                        "https://static.tvmaze.com/uploads/images/original_untouched/0/2313.jpg"
                    ),
                ),
                summary="<p>Summary 1 truncated</p>",
            )
        ),
        TVmazeSearchResult(
            show=TVmazeSearchResultShow(
                id=1059,
                name="Battlestar Galactica",
                genres=["Action", "Adventure", "Science-Fiction"],
                premiered=datetime.date(1978, 9, 17),
                ended=datetime.date(1979, 4, 29),
                network=TVmazeNetwork(
                    name="ABC", country=TVmazeCountry(name="United States")
                ),
                webChannel=None,
                image=TVmazeImage(
                    medium=HttpUrl(
                        "https://static.tvmaze.com/uploads/images/medium_portrait/6/17017.jpg"
                    ),
                    original=HttpUrl(
                        "https://static.tvmaze.com/uploads/images/original_untouched/6/17017.jpg"
                    ),
                ),
                summary="<p>Summary 2 truncated</p>",
            )
        ),
    ]
