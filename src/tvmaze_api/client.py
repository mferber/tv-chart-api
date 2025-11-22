from enum import StrEnum
from typing import Final

import httpx
import pydantic
from httpx import AsyncClient
from pydantic import TypeAdapter

import tvmaze_api.exceptions
from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO


class TVmazeAPIClient:
    BASE_URL: Final[str] = "https://api.tvmaze.com"

    class UrlPaths(StrEnum):
        SEARCH = "/search/shows"

    async def _get(self, relative_url: str, params: dict[str, str]) -> str:
        """Make a GET request to TVmaze.

        Args:
            relative_url: URL to fetch, relative to `BASE_URL`
            params: query params

        Returns:
            str: the unparsed response from the server
        """

        try:
            async with AsyncClient() as client:
                rsp = await client.get(self.BASE_URL + relative_url, params=params)
                rsp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise tvmaze_api.exceptions.ConnectionError from e
        # TODO: add exception type if auto-retry failed due to overloading the
        #    server (repeated 429 Too Many Requests)

        return rsp.text

    async def search_shows(self, query: str) -> list[TVmazeSearchResultDTO]:
        """Searches TVmaze for the given query string.

        Returns:
            List of `TVmazeSearchResultDTO`s encapsulating the search results
        """
        try:
            rsp_text = await self._get(self.UrlPaths.SEARCH, {"q": query})
            adapter = TypeAdapter(list[TVmazeSearchResultDTO])
            return adapter.validate_json(rsp_text)
        except pydantic.ValidationError as e:
            raise tvmaze_api.exceptions.InvalidResponseError from e
        except httpx.HTTPError as e:
            raise tvmaze_api.exceptions.ConnectionError from e
