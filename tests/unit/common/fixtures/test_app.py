from typing import Generator, Iterator

import pytest
from litestar import Litestar
from litestar.testing import TestClient
from testcontainers.postgres import PostgresContainer  # type: ignore

from app import create_app
from unit.common.utils.os_utils import temporarily_modified_environ
from unit.common.utils.req_utils import make_csrf_token_header

"""Fixtures that provide:

* A test app in a fixture, configured to use a Postgres database running
  in a testcontainer
* A CSRF header for use in unsafe requests
"""

TESTCONTAINER_POSTGRES_VERSION = 18


@pytest.fixture(scope="session")
def test_db_container() -> Generator[PostgresContainer, None, None]:
    """Creates a testcontainer running Postgres and yields its corresponding
    PostgresContainer object
    """

    with PostgresContainer(f"postgres:{TESTCONTAINER_POSTGRES_VERSION}") as postgres:
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
