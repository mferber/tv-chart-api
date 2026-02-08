# ruff: noqa I
# fmt: off

from unit.common.fixtures.app_testing import (
    # testable app configured with Postgres running in a testcontainer
    test_app,

    # Postgres testcontainer, used by test_app
    test_db_container,

    # Litestar TestClient for testing routes
    test_client,

    # Fetches CSRF token for unsafe queries by fetching /env
    csrf_token_header,

    # Logs in as one or more users before running test
    login_as_user
)

from unit.common.fixtures.httpx import (

    # patch httpx.AsyncClient.get to return a fixed response
    mocked_get,
    
    # patch httpx.AsyncClient.get to throw an exception
    mocked_get_with_network_failure,
)
