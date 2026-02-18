import asyncio
from typing import Iterator

import pytest
from helpers.test_data.db_setup import seed_test_db
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.postgres import PostgresContainer  # type: ignore

TESTCONTAINER_POSTGRES_VERSION = 18


@pytest.fixture(scope="session")
def test_db_container() -> Iterator[PostgresContainer]:
    """Creates a testcontainer running Postgres and yields its corresponding
    PostgresContainer object
    """

    with PostgresContainer(
        f"postgres:{TESTCONTAINER_POSTGRES_VERSION}", driver="asyncpg"
    ) as postgres:
        asyncio.run(seed_test_db(postgres))
        yield postgres


@pytest.fixture
def test_db_engine(test_db_container: PostgresContainer) -> Iterator[AsyncEngine]:
    yield create_async_engine(test_db_container.get_connection_url())
