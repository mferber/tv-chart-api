from litestar import Litestar, get


@get("/")
async def hello_world() -> str:
    return "hello world"


app = Litestar(route_handlers=[hello_world])
