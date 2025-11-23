"""Fixtures for mocking `httpx` responses."""

import httpx
import pytest

from unit.common.fixture_helpers.httpx import create_mock_httpx_async_client


@pytest.fixture
def mocked_get(mocker, request):
    """Patches `httpx.AsyncClient.get` to return a mocked response.

    Included by import in conftest.py — do not import directly!

    Takes parameters `(code, response_text)` where `code` is the status code to
    return and `response_text` is the text to use as the response.

    Requires the `httpx` module to be imported (`import httpx`) rather than
    just the client (`from httpx import AsyncClient` won't allow patching).

    Yields:
        Patched `get` method mock; can be checked for calls
    """

    code, response_text = request.param
    yield create_mock_httpx_async_client(mocker, code, response_text)


@pytest.fixture
def mocked_get_with_network_failure(mocker):
    """Patches `httpx.AsyncClient.get` to simulate a network failure.

    Included by import in conftest.py — do not import directly!

    Requires the `httpx` module to be imported (`import httpx`) rather than
    just the client (`from httpx import AsyncClient` won't allow patching).

    Yields:
        Patched `get` method mock; can be checked for calls
    """

    yield create_mock_httpx_async_client(
        mocker, 0, response_text="", exception=httpx.NetworkError("fake")
    )
