"""Domain models for TV show search results."""

from typing import Self

from html_sanitizer import Sanitizer  # type: ignore[import-untyped]
from pydantic import BaseModel, HttpUrl

from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO

# Set up HTML sanitizer for show summaries (we don't trust TVmaze, do we?)
configured_html_sanitizer = Sanitizer(
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


class SearchResult(BaseModel):
    """
    Encapsulates a single TVmaze search result.
    """

    tvmaze_id: int
    name: str
    genres: list[str] | None
    start_year: int | None
    end_year: int | None
    network: str | None
    network_country: str | None
    streaming_service: str | None
    streaming_service_country: str | None
    summary_html: str | None
    image_sm_url: HttpUrl | None
    image_lg_url: HttpUrl | None

    @classmethod
    def from_tvmaze_dto(cls, dto: TVmazeSearchResultDTO) -> Self:
        sanitized_summary_html = None
        if dto.show.summary:
            sanitized_summary_html = configured_html_sanitizer.sanitize(
                dto.show.summary
            )

        return cls(
            tvmaze_id=dto.show.id,
            name=dto.show.name,
            genres=dto.show.genres,
            start_year=dto.show.premiered.year if dto.show.premiered else None,
            end_year=dto.show.ended.year if dto.show.ended else None,
            network=dto.show.network.name if dto.show.network else None,
            network_country=(
                dto.show.network.country.name
                if dto.show.network and dto.show.network.country
                else None
            ),
            streaming_service=(
                dto.show.webChannel.name if dto.show.webChannel else None
            ),
            streaming_service_country=(
                dto.show.webChannel.country.name
                if dto.show.webChannel and dto.show.webChannel.country
                else None
            ),
            summary_html=sanitized_summary_html,
            image_sm_url=dto.show.image.medium if dto.show.image else None,
            image_lg_url=dto.show.image.original if dto.show.image else None,
        )


class SearchResults(BaseModel):
    """
    Encapsulates a TVmaze search result set.
    """

    results: list[SearchResult]

    @classmethod
    def from_tvmaze_dto_list(cls, dtos: list[TVmazeSearchResultDTO]) -> "SearchResults":
        return SearchResults(
            results=[SearchResult.from_tvmaze_dto(dto) for dto in dtos]
        )
