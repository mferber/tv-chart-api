"""
DTOs for reading search results from TVmaze search response.

See Also:
    `Show Search API docs <https://www.tvmaze.com/api#show-search>`_
"""

import datetime

from pydantic import BaseModel

from ..dtos import TVmazeNetworkDTO, TVmazeWebChannelDTO, TVmazeImageDTO


class TVmazeSearchResultShowDTO(BaseModel):
    """
    Encapsulates a single show representation in TVmaze search results.
    """

    id: int
    name: str
    genres: list[str] | None
    premiered: datetime.date | None
    ended: datetime.date | None
    network: TVmazeNetworkDTO | None
    webChannel: TVmazeWebChannelDTO | None
    image: TVmazeImageDTO | None
    summary: str | None


class TVmazeSearchResultDTO(BaseModel):
    """
    Top level DTO encapsulating a search result. TVmaze results are given as
    an array of objects that contain a `score` (which we ignore) and a `show`.
    See class method for handling of the array.
    """

    show: TVmazeSearchResultShowDTO
