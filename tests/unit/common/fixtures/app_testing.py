from typing import Generator, Iterator

import pytest
from litestar import Litestar
from litestar.testing import TestClient
from testcontainers.postgres import PostgresContainer  # type: ignore

from app import create_app
from unit.common.db.setup import seed_test_db
from unit.common.test_users import test_users
from unit.common.utils.os_utils import temporarily_modified_environ
from unit.common.utils.req_utils import make_csrf_token_header

"""Fixtures that provide:

* A test app instance, configured to use a Postgres database running in a testcontainer
* The Postgres testcontainer itself
* A CSRF header for use in unsafe requests
* A Litestar TestClient for testing Litestar routes, pointing at the test app instance
* A CSRF token header that must be included with all "unsafe" app requests for validation
* A logged-in user; parametrizable to specify which user (see test_users.py)
"""

TESTCONTAINER_POSTGRES_VERSION = 18


@pytest.fixture(scope="session")
def test_db_container() -> Generator[PostgresContainer, None, None]:
    """Creates a testcontainer running Postgres and yields its corresponding
    PostgresContainer object
    """

    with PostgresContainer(f"postgres:{TESTCONTAINER_POSTGRES_VERSION}") as postgres:
        seed_test_db(postgres)
        yield postgres


@pytest.fixture
def test_app(test_db_container: PostgresContainer) -> Generator[Litestar, None, None]:
    """Yields a testable app instance using a Postgres testcontainer as its db, overriding
    .env
    """

    with temporarily_modified_environ(
        APP_ENV="testing",
        DB_DRIVER="postgresql+asyncpg",
        DB_USER=test_db_container.username,
        DB_PASS=test_db_container.password,
        DB_HOST=test_db_container.get_container_host_ip(),
        DB_PORT=str(test_db_container.get_exposed_port(5432)),
        DB_NAME=test_db_container.dbname,
    ):
        yield create_app()


@pytest.fixture
def test_client(test_app: Litestar) -> Iterator[TestClient[Litestar]]:
    """Yields a TestClient set up to test the app instance provided by test_app"""

    with TestClient(app=test_app) as test_client:
        yield test_client


@pytest.fixture
def csrf_token_header(test_client: TestClient[Litestar]) -> dict[str, str]:
    """Generates a CSRF header for inclusion in unsafe requests, by running a safe GET
    and reading the resulting cookie (which is also automatically stored in the client
    to be returned automatically as a cookie in subsequent requests)
    """

    rsp = test_client.get("/env")  # automatically stores the cookie
    return make_csrf_token_header(rsp.cookies["csrftoken"])


@pytest.fixture
def login_as_user(
    test_client: TestClient[Litestar],
    csrf_token_header: dict[str, str],
    request: pytest.FixtureRequest,
) -> None:
    """Logs in as one or more users before running the attached test.

    Parametrize the test as follows:

    ```
    @pytest.mark.parametrize('login_as_user', ["test_user1"], indirect=True)
    def test...():
        ...
    ```

    Test users (`test_user1` in this example) are defined in `tests/unit/common/test_users.py`.

    If the test should be run for more than one user, include multiple test user ids in the list.

    Note about the way parametrized fixtures work: the parameter value is made available to
    the fixture via the `request` parameter, specifically in `request.param`. This is confusing.
    """

    test_user_id = request.param
    test_user_info = test_users.get(request.param)
    if test_user_info is None:
        raise Exception(f"Unrecognized test user: {test_user_id}")

    [email, password] = test_user_info

    # successfully accessing this endpoint yields JWT cookie for future requests
    rsp = test_client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers=csrf_token_header,
    )
    rsp.raise_for_status()
