"""Tests for the TVmaze API client.

Tests are to confirm basic behavior, test encapsulation into models, and ensure
that the right TVmaze URLs are being called.

Only minimal response documents are tested. More variations will be tested through
the service layer, where we also test conversion to app domain models.
"""

import datetime

import httpx
import pytest
import respx
from pydantic import HttpUrl
from pytest_mock import MockerFixture

from tvmaze_api.client import (
    ConnectionError,
    InvalidResponseError,
    RateLimitedError,
    TVmazeAPIClient,
)
from tvmaze_api.models import (
    TVmazeCountry,
    TVmazeImage,
    TVmazeNetwork,
    TVmazeSearchResult,
    TVmazeSearchResultShow,
)

from .sample_tvmaze_responses.reader import read_sample


@pytest.mark.asyncio
async def test_search_request(respx_mock: respx.MockRouter) -> None:
    text = read_sample("multiple_results.json")
    route = respx_mock.route(method="GET").respond(text=text)
    client = TVmazeAPIClient()

    rsp = await client.search_shows("query")

    # verify TVmaze was called correctly
    assert route.call_count == 1
    url = route.calls.last.request.url
    assert url.path == "/search/shows"
    assert dict(url.params) == {"q": "query"}

    # verify we extracted the expected pydantic model
    expected = pydantic_model_battlestar_galactica()
    assert rsp.root == expected


@pytest.mark.asyncio
async def test_invalid_response_raises(respx_mock: respx.MockRouter) -> None:
    text = read_sample("multiple_results_invalid.json")
    route = respx_mock.route(method="GET").respond(text=text)

    with pytest.raises(InvalidResponseError):
        client = TVmazeAPIClient()

        try:
            await client.search_shows("query")
        except InvalidResponseError:
            assert route.call_count == 1
            raise


@pytest.mark.asyncio
async def test_failing_request_raises(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.route(method="GET").respond(status_code=500)

    with pytest.raises(ConnectionError):
        client = TVmazeAPIClient()

        try:
            await client.search_shows("query")
        except ConnectionError:
            print("here")
            assert route.call_count == 1
            raise


@pytest.mark.asyncio
async def test_network_error_raises(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.route(method="GET").mock(side_effect=httpx.NetworkError("fake"))
    with pytest.raises(ConnectionError):
        client = TVmazeAPIClient()

        try:
            await client.search_shows("query")
        except Exception:
            assert route.call_count == 1
            raise


@pytest.mark.asyncio
async def test_rate_limited_request_raises_after_using_up_attempts(
    respx_mock: respx.MockRouter, mocker: MockerFixture
) -> None:
    """TVmaze throttles use of its free API so this could happen."""

    mocker.patch.object(TVmazeAPIClient, "RETRY_BACKOFF_FACTOR", new=0.01)
    route = respx_mock.route(method="GET").respond(
        status_code=httpx.codes.TOO_MANY_REQUESTS
    )

    with pytest.raises(RateLimitedError):
        client = TVmazeAPIClient()

        try:
            await client.search_shows("query")
        except Exception:
            assert route.call_count == TVmazeAPIClient.RETRY_LIMIT
            raise


# --- Helpers ---


def pydantic_model_battlestar_galactica() -> list[TVmazeSearchResult]:
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
