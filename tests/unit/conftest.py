# ruff: noqa I
# fmt: off

from unit.common.fixtures.test_app import (
    # testable app configured with Postgres running in a testcontainer
    test_app,

    # Postgres testcontainer, used by test_app
    test_db_container,

    # Litestar TestClient for testing routes
    test_client,
)

from unit.common.fixtures.httpx import (

    # patch httpx.AsyncClient.get to return a fixed response
    mocked_get,
    
    # patch httpx.AsyncClient.get to throw an exception
    mocked_get_with_network_failure,
)
