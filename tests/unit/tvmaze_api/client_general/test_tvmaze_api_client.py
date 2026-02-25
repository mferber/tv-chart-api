"""Tests for the TVmaze API client.

Tests are to confirm basic behavior, test encapsulation into models, and ensure
that the right TVmaze URLs are being called.

Only minimal response documents are tested. More variations will be tested through
the service layer, where we also test conversion to app domain models.
"""

import httpx
import pytest
import respx
from helpers.testing_data.mock_responses.reader import SampleFileReader
from pytest_mock import MockerFixture

from tvmaze_api.client import (
    ConnectionError,
    RateLimitedError,
    TVmazeAPIClient,
)

sample_file_reader = SampleFileReader("sample_tvmaze_search_results")


@pytest.mark.asyncio
async def test_failing_request_raises(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.route(method="GET").respond(status_code=500)

    with pytest.raises(ConnectionError):
        client = TVmazeAPIClient()

        try:
            await client.test_query()
        except ConnectionError:
            assert route.call_count == 1
            raise


@pytest.mark.asyncio
async def test_network_error_raises(respx_mock: respx.MockRouter) -> None:
    route = respx_mock.route(method="GET").mock(side_effect=httpx.NetworkError("fake"))
    with pytest.raises(ConnectionError):
        client = TVmazeAPIClient()

        try:
            await client.test_query()
        except Exception as e:
            print(repr(e))
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
            await client.test_query()
        except Exception:
            assert route.call_count == TVmazeAPIClient.RETRY_LIMIT
            raise
