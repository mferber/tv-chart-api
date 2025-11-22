import asyncio
from enum import StrEnum
from typing import Final

import httpx
import pydantic
from pydantic import TypeAdapter

import tvmaze_api.exceptions
from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO


class TVmazeAPIClient:
    BASE_URL: Final[str] = "https://api.tvmaze.com"

    # In the unlikely event that we exceed request limits on TVmaze, they have a
    # fairly harsh retry policy, currently something like 20 calls per 10 seconds.
    # So we're going with a fairly large backoff interval to maximize our chance of
    # eventually succeeding.
    RETRY_LIMIT = 4  # including the first try
    RETRY_BACKOFF_FACTOR = 3

    class UrlPaths(StrEnum):
        SEARCH = "/search/shows"

    async def _get(self, relative_url: str, params: dict[str, str]) -> str:
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

        except httpx.HTTPStatusError as e:
            if e.response.status_code == httpx.codes.TOO_MANY_REQUESTS:
                raise tvmaze_api.exceptions.RateLimitedError from e
            raise tvmaze_api.exceptions.ConnectionError from e

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
