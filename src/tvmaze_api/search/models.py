from pydantic import BaseModel, HttpUrl


class SearchResult(BaseModel):
    """
    Response model encapsulating a single TVmaze search result.
    """

    tvmaze_id: int
    name: str
    genres: list[str]
    start_year: int | None
    end_year: int | None
    network: str | None
    network_country: str | None
    web_host: str | None
    web_host_country: str | None
    summary_html: str | None
    image_url: HttpUrl | None


class SearchResults(BaseModel):
    """
    Response model encapsulating a TVmaze search result set.
    """

    results: list[SearchResult]
