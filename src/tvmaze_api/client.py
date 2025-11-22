from enum import StrEnum
from typing import Final

from httpx import AsyncClient, HTTPError


class TVmazeAPIClient:
    class Exceptions:
        class ConnectionError(Exception):
            pass

    BASE_URL: Final[str] = "https://api.tvmaze.com"

    class UrlPaths(StrEnum):
        SEARCH = "/show/search"

    async def get(self, relative_url: str, params: dict[str, str]) -> str:
        """
        Make a GET request to TVmaze.

        Args:
            url: URL to fetch
            params: query params

        Returns:
            str: the unparsed response from the server
        """

        try:
            async with AsyncClient() as client:
                rsp = await client.get(self.BASE_URL + relative_url, params=params)
                rsp.raise_for_status()
        except HTTPError as e:
            raise self.Exceptions.ConnectionError(e)
        # TODO: add exception type if auto-retry failed due to overloading the
        #    server (repeated 429 Too Many Requests)

        return rsp.text

    async def search_shows(self, query: str) -> str:
        return await self.get(self.UrlPaths.SEARCH, {"q": query})
