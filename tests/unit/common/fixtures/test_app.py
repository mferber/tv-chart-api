from typing import Generator

import pytest
from litestar import Litestar
from testcontainers.postgres import PostgresContainer  # type: ignore

from app import create_app
from unit.common.utils.utils import temporarily_modified_environ

TESTCONTAINER_POSTGRES_VERSION = 18


@pytest.fixture(scope="session")
def test_db_container() -> Generator[PostgresContainer, None, None]:
    """Creates a testcontainer running Postgres and yields its corresponding
    PostgresContainer object"""

    with PostgresContainer(f"postgres:{TESTCONTAINER_POSTGRES_VERSION}") as postgres:
        yield postgres


@pytest.fixture
def test_app(test_db_container: PostgresContainer) -> Generator[Litestar, None, None]:
    """Yields a testable app instance using a Postgres testcontainer as its db, overriding
    .env"""

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
