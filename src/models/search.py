from pydantic import BaseModel, HttpUrl


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


class SearchResults(BaseModel):
    """
    Encapsulates a TVmaze search result set.
    """

    results: list[SearchResult]
