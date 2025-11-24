from litestar import Litestar, get

from services.search import SearchResults, SearchService


@get("/search")
async def search(q: str) -> SearchResults:
    result = await SearchService().search(q)
    return result


app = Litestar(route_handlers=[search])
