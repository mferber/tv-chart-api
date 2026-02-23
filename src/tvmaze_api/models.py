"""
Models for TVmaze API responses.
"""

import datetime
from typing import Self

from pydantic import BaseModel, HttpUrl

from models.search import SearchResult, SearchResults
from tvmaze_api.utils.html_sanitizer import html_sanitizer


class TVmazeCountry(BaseModel):
    name: str


class TVmazeNetwork(BaseModel):
    name: str
    country: TVmazeCountry | None


class TVmazeWebChannel(BaseModel):
    name: str
    country: TVmazeCountry | None


class TVmazeImage(BaseModel):
    medium: HttpUrl | None
    original: HttpUrl | None


class TVmazeSearchResultShow(BaseModel):
    """
    Encapsulates a single show representation in TVmaze search results.
    """

    id: int
    name: str
    genres: list[str] | None
    premiered: datetime.date | None
    ended: datetime.date | None
    network: TVmazeNetwork | None
    webChannel: TVmazeWebChannel | None
    image: TVmazeImage | None
    summary: str | None


class TVmazeSearchResult(BaseModel):
    """
    Top level DTO encapsulating a search result. TVmaze results are given as
    an array of objects that contain a `score` (which we ignore) and a `show`.
    See class method for handling of the array.
    """

    show: TVmazeSearchResultShow

    def to_search_result_model(self) -> SearchResult:
        sanitized_summary_html = None
        if self.show.summary:
            sanitized_summary_html = html_sanitizer().sanitize(self.show.summary)

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
