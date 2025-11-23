"""Domain models for TV show search results."""

from pydantic import BaseModel, HttpUrl

from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO


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
    image_url: HttpUrl | None

    @classmethod
    def from_tvmaze_dto(cls, dto: TVmazeSearchResultDTO):
        return SearchResult(
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
            summary_html=dto.show.summary,
            image_url=dto.show.image.medium if dto.show.image else None,
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
