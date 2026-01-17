from typing import Any

import httpx
from pytest_mock import MockerFixture


def create_mock_httpx_async_client(
    mocker: MockerFixture,
    status_code: int,
    /,
    response_text: str,
    exception: Exception | None = None,
) -> Any:
    """Helper: patches `AsyncClient.get` to return a mocked response.

    Requires the `httpx` module to be imported (`import httpx`) rather than
    just the client (`from httpx import AsyncClient` won't allow patching).

    Args:
        status_code: response status code to mock
        response_text: body of the mocked response
        exception: exception to raise instead of mocking a response

    Returns:
        Patched `get` method mock; can be checked for calls
    """

    mock_client = mocker.AsyncMock()

    if exception is None:
        mock_response = httpx.Response(
            status_code=status_code, text=response_text, request=mocker.Mock()
        )
        mock_client.get.return_value = mock_response
    else:
        mock_client.get.side_effect = exception

    # patch AsyncClient to return our mock client as a context manager
    mocker.patch(
        "httpx.AsyncClient",
        return_value=mocker.AsyncMock(
            __aenter__=mocker.AsyncMock(return_value=mock_client),
            __aexit__=mocker.AsyncMock(return_value=None),
        ),
    )
    return mock_client.get
