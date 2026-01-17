from unittest.mock import AsyncMock

import pytest

import services.search.exceptions
from services.search import SearchService

from .sample_tvmaze_responses.reader import read_sample


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mocked_get", [(200, read_sample("multiple_results.json"))], indirect=True
)
async def test_search_service(mocked_get: AsyncMock) -> None:
    svc = SearchService()
    result = await svc.search("Battlestar Galactica")
    print(result)  # TODO


@pytest.mark.asyncio
@pytest.mark.parametrize("mocked_get", [(500, "")], indirect=True)
async def test_search_service_server_error(mocked_get: AsyncMock) -> None:
    with pytest.raises(services.search.exceptions.SearchError):
        svc = SearchService()
        result = await svc.search("Battlestar Galactica")
        print(result)  # TODO
