from models.search import SearchResults
from tvmaze_api.client import TVmazeAPIClient
from tvmaze_api.models import TVmazeSearchResult


class SearchError(Exception):
    """An error occurred while attempting a search.

    Consult `__cause__` to see the source of the error.
    """

    pass


class SearchService:
    async def search(self, query: str) -> SearchResults:
        """Search for TV shows matching the query.

        Returns:
            A `SearchResults` encapsulating the results. Will contain an
            empty `results` list if no matches.

        Raises:
            `SearchError` if the search cannot be completed successfully.
        """

        try:
            tvmaze_results = await TVmazeAPIClient().search_shows(query)
            return TVmazeSearchResult.to_search_results_model(tvmaze_results)
        except Exception as e:
            raise SearchError from e
