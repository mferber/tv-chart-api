"""
DTOs for reading search results from TVmaze search response.

See Also:
    `Search API docs <https://www.tvmaze.com/api#show-search>`_
"""

import datetime

from pydantic import BaseModel, TypeAdapter

from .models import SearchResults, SearchResult
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
    See class methods for handling of the array.
    """

    show: TVmazeSearchResultShowDTO

    def to_search_result(self) -> SearchResult:
        return SearchResult(
            tvmaze_id=self.show.id,
            name=self.show.name,
            genres=self.show.genres,
            start_year=self.show.premiered.year if self.show.premiered else None,
            end_year=self.show.ended.year if self.show.ended else None,
            network=self.show.network.name if self.show.network else None,
            network_country=self.show.network.country.name
            if self.show.network and self.show.network.country
            else None,
            web_host=self.show.webChannel.name if self.show.webChannel else None,
            web_host_country=self.show.webChannel.country.name
            if self.show.webChannel and self.show.webChannel.country
            else None,
            summary_html=self.show.summary,
            image_url=self.show.image.medium if self.show.image else None,
        )

    @classmethod
    def list_from_tvmaze_response(
        cls, response_json: str
    ) -> list["TVmazeSearchResultDTO"]:
        """
        Validates a JSON array of results from TVmaze into a list of DTOs.
        """

        adapter = TypeAdapter(list[TVmazeSearchResultDTO])
        return adapter.validate_json(response_json)

    @classmethod
    def list_to_search_results(
        cls, lst: list["TVmazeSearchResultDTO"]
    ) -> SearchResults:
        """
        Creates a SearchResults model from list of DTOs.
        """

        return SearchResults(results=[dto.to_search_result() for dto in lst])
