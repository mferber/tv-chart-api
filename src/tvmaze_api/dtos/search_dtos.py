"""
DTOs for reading search results from TVmaze search response.

See Also:
    `Show Search API docs <https://www.tvmaze.com/api#show-search>`_
"""

import datetime
from typing import Self

from html_sanitizer import Sanitizer  # type: ignore[import-untyped]
from pydantic import BaseModel

from models.search import SearchResult, SearchResults

from .common_dtos import TVmazeImageDTO, TVmazeNetworkDTO, TVmazeWebChannelDTO

# Set up HTML sanitizer for show summaries (we don't trust TVmaze, do we?)
_configured_html_sanitizer = Sanitizer(
    {
        "tags": {  # tags retained in sanitized html; defaults minus <a>
            "h1",
            "h2",
            "h3",
            "strong",
            "em",
            "p",
            "ul",
            "ol",
            "li",
            "br",
            "sub",
            "sup",
            "hr",
        },
        "attributes": {},
        "empty": {"hr", "br"},  # tags retained even if empty
        "separate": {"p", "li"},  # will not be merged with siblings
        "whitespace": set(),
        "keep_typographic_whitespace": True,
    }
)


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

    def to_search_result_model(self) -> SearchResult:
        sanitized_summary_html = None
        if self.show.summary:
            sanitized_summary_html = _configured_html_sanitizer.sanitize(
                self.show.summary
            )

        return SearchResult(
            tvmaze_id=self.show.id,
            name=self.show.name,
            genres=self.show.genres,
            start_year=self.show.premiered.year if self.show.premiered else None,
            end_year=self.show.ended.year if self.show.ended else None,
            network=self.show.network.name if self.show.network else None,
            network_country=(
                self.show.network.country.name
                if self.show.network and self.show.network.country
                else None
            ),
            streaming_service=(
                self.show.webChannel.name if self.show.webChannel else None
            ),
            streaming_service_country=(
                self.show.webChannel.country.name
                if self.show.webChannel and self.show.webChannel.country
                else None
            ),
            summary_html=sanitized_summary_html,
            image_sm_url=self.show.image.medium if self.show.image else None,
            image_lg_url=self.show.image.original if self.show.image else None,
        )

    @classmethod
    def to_search_results_model(cls, result_dtos: list[Self]) -> SearchResults:
        return SearchResults(
            results=[dto.to_search_result_model() for dto in result_dtos]
        )
