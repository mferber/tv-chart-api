from tvmaze_api.client import TVmazeAPIClient

from .exceptions import SearchError
from .models import SearchResults


class SearchService:
    async def search(self, query: str) -> str:  # SearchResults:
        """Search for TV shows matching the query.

        Returns:
            A `SearchResults` encapsulating the results. Will contain an
            empty `results` list if no matches.

        Raises:
            `SearchError` if the search cannot be completed successfully.
        """

        try:
            tvmazeDtos = await TVmazeAPIClient().search_shows(query)
            return SearchResults.from_tvmaze_dto_list(tvmazeDtos)
        except Exception as e:
            print("Exception", e)
            raise SearchError from e
