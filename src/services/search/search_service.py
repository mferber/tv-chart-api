from models.search import SearchResults
from tvmaze_api.client import TVmazeAPIClient
from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO

from .exceptions import SearchError


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
            tvmazeDtos = await TVmazeAPIClient().search_shows(query)
            return TVmazeSearchResultDTO.to_search_results_model(tvmazeDtos)
        except Exception as e:
            raise SearchError from e
