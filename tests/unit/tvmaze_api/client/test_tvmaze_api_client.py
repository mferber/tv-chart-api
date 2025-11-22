"""Tests for the TVmaze API client.

Tests are to confirm basic behavior, test encapsulation into models, and ensure
that the right TVmaze URLs are being called.

Only minimal response documents are tested. More variations will be tested through
the service layer, where we also test conversion to app domain models.
"""

import datetime
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import HttpUrl

import tvmaze_api.exceptions
from tvmaze_api.client import TVmazeAPIClient
from tvmaze_api.dtos.common_dtos import (
    TVmazeCountryDTO,
    TVmazeImageDTO,
    TVmazeNetworkDTO,
)
from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO, TVmazeSearchResultShowDTO

from .sample_tvmaze_responses.reader import read_sample

# --- Fixtures ---


def mock_httpx_async_client(
    mocker,
    status_code: int,
    /,
    response_text_name: str,
    exception: Exception | None = None,
) -> AsyncMock:
    """Helper: mocks AsyncClient to return a fake response.

    Args:
        status_code: response status code to mock
        response_text_name: file name from `sample_tvmaze_responses` to use for mock
            content; if file doesn't exist, the name will be used as the literal
            response content
        exception: exception to raise instead of mocking a response
    """

    try:
        text = read_sample(response_text_name)
    except Exception:
        text = response_text_name

    mock_client = mocker.AsyncMock()

    if exception is None:
        mock_response = httpx.Response(
            status_code=status_code, text=text, request=mocker.Mock()
        )
        mock_client.get.return_value = mock_response
    else:
        mock_client.get.side_effect = exception

    # patch AsyncClient to return our mock client as a context manager
    mocker.patch(
        "tvmaze_api.client.AsyncClient",
        return_value=mocker.AsyncMock(
            __aenter__=mocker.AsyncMock(return_value=mock_client),
            __aexit__=mocker.AsyncMock(return_value=None),
        ),
    )
    return mock_client.get


@pytest.fixture
def mocked_get(mocker, request):
    """Sets up a mock request.

    Takes parameters `(code, response_text_name)` where `code` is the status code to
    return and `response_text_name` is the filename from sample_tvmaze_responses to use
    as the response. If the file doesn't exist, the value of `response_text_name` is
    used as the literal response.
    """

    code, response_text_name = request.param
    return mock_httpx_async_client(mocker, code, response_text_name=response_text_name)


@pytest.fixture
def mocked_get_with_network_failure(mocker):
    """Sets up a mock request that simulates a network failure."""

    return mock_httpx_async_client(
        mocker, 0, response_text_name="", exception=httpx.NetworkError("fake")
    )


# --- Tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize("mocked_get", [(200, "multiple_results.json")], indirect=True)
async def test_search_request(mocked_get):
    client = TVmazeAPIClient()
    rsp = await client.search_shows("query")

    # verify TVmaze was called correctly
    mocked_get.assert_called_once()
    get_args = mocked_get.call_args
    assert get_args.args == ("https://api.tvmaze.com/show/search",)
    assert get_args.kwargs["params"] == {"q": "query"}

    # verify we extracted the expected pydantic model
    expected = pydantic_model_battlestar_galactica()
    assert rsp == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mocked_get", [(200, "multiple_results_invalid.json")], indirect=True
)
async def test_invalid_response_raises(mocked_get):
    with pytest.raises(tvmaze_api.exceptions.InvalidResponseError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except tvmaze_api.exceptions.InvalidResponseError:
            mocked_get.assert_called_once()
            raise


@pytest.mark.asyncio
@pytest.mark.parametrize("mocked_get", [(500, "content doesn't matter")], indirect=True)
async def test_failing_request_raises(mocked_get):
    with pytest.raises(tvmaze_api.exceptions.ConnectionError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except tvmaze_api.exceptions.ConnectionError:
            mocked_get.assert_called_once()
            raise


@pytest.mark.asyncio
async def test_network_error_raises(mocked_get_with_network_failure):
    with pytest.raises(tvmaze_api.exceptions.ConnectionError):
        client = TVmazeAPIClient()
        await client.search_shows("query")


@pytest.mark.asyncio
@pytest.mark.parametrize("mocked_get", [(500, "content doesn't matter")], indirect=True)
async def test_request_exception_raises(mocked_get):
    pass


# --- Helpers ---


def pydantic_model_battlestar_galactica():
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
