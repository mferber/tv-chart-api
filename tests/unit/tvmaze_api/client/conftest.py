from typing import Iterator

import httpx
import pytest
from pytest_mock import MockerFixture

from tvmaze_api.client import TVmazeAPIClient
from unit.common.fixture_helpers.httpx import create_mock_httpx_async_client


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
