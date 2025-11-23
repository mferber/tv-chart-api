# ruff: noqa I
# fmt: off

from unit.common.fixtures.httpx import (

    # patch httpx.AsyncClient.get to return a fixed response
    mocked_get,
    
    # patch httpx.AsyncClient.get to throw an exception
    mocked_get_with_network_failure,
)
