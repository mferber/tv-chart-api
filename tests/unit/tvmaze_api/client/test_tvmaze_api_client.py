"""Tests for the TVmaze API client.

Tests are to confirm basic behavior and ensure that the right TVmaze
URLs are being called.
"""
from unittest.mock import AsyncMock

import httpx
import pytest

from tvmaze_api.client import TVmazeAPIClient


def mock_httpx_async_client(mocker, status_code: int) -> AsyncMock:
    """Helper: mocks AsyncClient to return a fake response and the specified status code."""

    mock_response = httpx.Response(
        status_code=status_code, text="TESTING", request=mocker.Mock()
    )
    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_response

    # Patch AsyncClient to return our mock client as a context manager
    mocker.patch(
        "tvmaze_api.client.AsyncClient",
        return_value=mocker.AsyncMock(
            __aenter__=mocker.AsyncMock(return_value=mock_client),
            __aexit__=mocker.AsyncMock(return_value=None),
        ),
    )
    return mock_client.get


@pytest.fixture
def successful_mock_get(mocker):
    """Use fixture to make mock request succeed. Returns the mocked `get` method
    for assertions.
    """
    return mock_httpx_async_client(mocker, 200)


@pytest.fixture
def unsuccessful_mock_get(mocker):
    """Use fixture to make mock request fail. Returns the mocked `get` method
    for assertions.
    """
    return mock_httpx_async_client(mocker, 500)


@pytest.mark.asyncio
async def test_search_request(successful_mock_get):
    client = TVmazeAPIClient()
    await client.search_shows("query")

    successful_mock_get.assert_called_once()
    get_args = successful_mock_get.call_args
    assert get_args.args == ("https://api.tvmaze.com/show/search",)
    assert get_args.kwargs["params"] == {"q": "query"}


@pytest.mark.asyncio
async def test_failing_request_raises(unsuccessful_mock_get):
    with pytest.raises(TVmazeAPIClient.Exceptions.ConnectionError):
        client = TVmazeAPIClient()
        try:
            await client.search_shows("query")
        except:
            unsuccessful_mock_get.assert_called_once()
            raise
