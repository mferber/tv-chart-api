import asyncio
from enum import StrEnum
from typing import Final

import httpx
import pydantic

from tvmaze_api.models import TVmazeSearchResultList


class ConnectionError(Exception):
    pass


class RateLimitedError(Exception):
    pass


class InvalidResponseError(Exception):
    pass


class TVmazeAPIClient:
    BASE_URL: Final[str] = "https://api.tvmaze.com"

    # In the unlikely event that we exceed request limits on TVmaze, they have a
    # fairly harsh retry policy, currently something like 20 calls per 10 seconds.
    # So we're going with a fairly large backoff interval to maximize our chance of
    # eventually succeeding.
    RETRY_LIMIT = 4  # including the first try
    RETRY_BACKOFF_FACTOR = 3

    class UrlPaths(StrEnum):
        TEST = "/shows/1"
        SEARCH = "/search/shows"

    async def _get(self, relative_url: str, params: dict[str, str] | None) -> str:
        """Make a GET request to TVmaze.

        If rate-limited by server, retries some number of times with exponential
        backoff before giving up.

        Args:
            relative_url: URL to fetch, relative to `BASE_URL`
            params: query params

        Returns:
            str: the unparsed response from the server
        """
        try:
            async with httpx.AsyncClient() as client:
                # couldn't get httpx-retries to work, had to roll my own retry logic
                try_count = 1
                while True:
                    try:
                        rsp = await client.get(
                            self.BASE_URL + relative_url, params=params
                        )
                        rsp.raise_for_status()

                    except httpx.HTTPStatusError as e:  # check for rate-limiting
                        if e.response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                            if try_count >= self.RETRY_LIMIT:
                                raise  # ran out of retries

                            delay = self.RETRY_BACKOFF_FACTOR * (2 ** (try_count - 1))
                            await asyncio.sleep(delay)
                            try_count += 1
                            continue

                        raise  # something went wrong but it wasn't rate-limiting

                    break  # no error: end the retry loop

        except httpx.HTTPError as e:
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                    raise RateLimitedError from e
            raise ConnectionError from e

        return rsp.text

    async def test_query(self) -> None:
        """Makes a test query to TVmaze, for testing purposes only. The content
        of the request doesn't matter."""
        await self._get(self.UrlPaths.TEST, None)

    async def search_shows(self, query: str) -> TVmazeSearchResultList:
        """Searches TVmaze for the given query string.

        Returns:
            List of `TVmazeSearchResult`s encapsulating the search results
        """
        try:
            rsp_text = await self._get(self.UrlPaths.SEARCH, {"q": query})
            return TVmazeSearchResultList.model_validate_json(rsp_text)
        except pydantic.ValidationError as e:
            raise InvalidResponseError from e
