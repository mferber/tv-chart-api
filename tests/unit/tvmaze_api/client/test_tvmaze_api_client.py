"""Tests for the TVmaze API client.

Tests are to confirm basic behavior, test encapsulation into models, and ensure
that the right TVmaze URLs are being called.

Only minimal response documents are tested. More variations will be tested through
the service layer, where we also test conversion to app domain models.
"""

import datetime
from typing import Iterator
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import HttpUrl
from pytest_mock import MockerFixture

import tvmaze_api.exceptions
from tvmaze_api.client import TVmazeAPIClient
from tvmaze_api.dtos.common_dtos import (
    TVmazeCountryDTO,
    TVmazeImageDTO,
    TVmazeNetworkDTO,
)
from tvmaze_api.dtos.search_dtos import (
    TVmazeSearchResultDTO,
    TVmazeSearchResultShowDTO,
)
from unit.common.fixture_helpers.httpx import create_mock_httpx_async_client

from .sample_tvmaze_responses.reader import read_sample

# --- Fixtures ---


@pytest.fixture
def mocked_get_with_rate_limiting_failure(
    mocker: MockerFixture,
) -> Iterator[httpx.AsyncClient]:
    """Sets up a mock request that simulates repeated 429 Too Many Requests errors."""

    # reduce the backoff time to something negligible for testing
    mocker.patch.object(TVmazeAPIClient, "RETRY_BACKOFF_FACTOR", new=0.01)

    mock_response = mocker.Mock(
        spec=httpx.Response, status_code=httpx.codes.TOO_MANY_REQUESTS
    )
    too_many_requests_exception = httpx.HTTPStatusError(
        "simulated 429", request=mocker.Mock(), response=mock_response
    )
    mock_response.raise_for_status.side_effect = too_many_requests_exception

    yield create_mock_httpx_async_client(
        mocker, httpx.codes.TOO_MANY_REQUESTS, response_text=""
    )


# --- Tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mocked_get", [(200, read_sample("multiple_results.json"))], indirect=True
)
async def test_search_request(mocked_get: AsyncMock) -> None:
    client = TVmazeAPIClient()
    rsp = await client.search_shows("query")

    # verify TVmaze was called correctly
    mocked_get.assert_called_once()
    get_args = mocked_get.call_args
    assert get_args.args == ("https://api.tvmaze.com/search/shows",)
    assert get_args.kwargs["params"] == {"q": "query"}

    # verify we extracted the expected pydantic model
    expected = pydantic_model_battlestar_galactica()
    assert rsp == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mocked_get", [(200, "multiple_results_invalid.json")], indirect=True
)
async def test_invalid_response_raises(mocked_get: AsyncMock) -> None:
    with pytest.raises(tvmaze_api.exceptions.InvalidResponseError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except tvmaze_api.exceptions.InvalidResponseError:
            mocked_get.assert_called_once()
            raise


@pytest.mark.asyncio
@pytest.mark.parametrize("mocked_get", [(500, "content doesn't matter")], indirect=True)
async def test_failing_request_raises(mocked_get: AsyncMock) -> None:
    with pytest.raises(tvmaze_api.exceptions.ConnectionError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except tvmaze_api.exceptions.ConnectionError:
            mocked_get.assert_called_once()
            raise


@pytest.mark.asyncio
async def test_network_error_raises(mocked_get_with_network_failure: AsyncMock) -> None:
    with pytest.raises(tvmaze_api.exceptions.ConnectionError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except Exception:
            mocked_get_with_network_failure.assert_called_once()
            raise


@pytest.mark.asyncio
async def test_rate_limited_request_raises_after_using_up_attempts(
    mocked_get_with_rate_limiting_failure: AsyncMock,
) -> None:
    """TVmaze throttles use of its free API so this could happen."""

    with pytest.raises(tvmaze_api.exceptions.RateLimitedError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except Exception:
            assert (
                mocked_get_with_rate_limiting_failure.call_count
                == TVmazeAPIClient.RETRY_LIMIT
            )
            raise


@pytest.mark.asyncio
@pytest.mark.parametrize("mocked_get", [(500, "content doesn't matter")], indirect=True)
async def test_request_exception_raises(mocked_get: AsyncMock) -> None:
    pass


# --- Helpers ---


def pydantic_model_battlestar_galactica() -> list[TVmazeSearchResultDTO]:
    return [
        TVmazeSearchResultDTO(
            show=TVmazeSearchResultShowDTO(
                id=166,
                name="Battlestar Galactica",
                genres=["Drama", "Science-Fiction", "War"],
                premiered=datetime.date(2003, 12, 8),
                ended=datetime.date(2009, 10, 27),
                network=TVmazeNetworkDTO(
                    name="Syfy", country=TVmazeCountryDTO(name="United States")
                ),
                webChannel=None,
                image=TVmazeImageDTO(
                    medium=HttpUrl(
                        "https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg"
                    )
                ),
                summary="<p>Summary 1 truncated</p>",
            )
        ),
        TVmazeSearchResultDTO(
            show=TVmazeSearchResultShowDTO(
                id=1059,
                name="Battlestar Galactica",
                genres=["Action", "Adventure", "Science-Fiction"],
                premiered=datetime.date(1978, 9, 17),
                ended=datetime.date(1979, 4, 29),
                network=TVmazeNetworkDTO(
                    name="ABC", country=TVmazeCountryDTO(name="United States")
                ),
                webChannel=None,
                image=TVmazeImageDTO(
                    medium=HttpUrl(
                        "https://static.tvmaze.com/uploads/images/medium_portrait/6/17017.jpg"
                    )
                ),
                summary="<p>Summary 2 truncated</p>",
            )
        ),
    ]
