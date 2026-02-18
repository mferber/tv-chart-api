import asyncio
from typing import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from helpers.test_data.db_setup import seed_test_db
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
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


@pytest_asyncio.fixture
async def autorollback_db_session(
    test_db_engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    """Provides an AsyncSession where changes committed in the session will be automatically
    rolled back at the end of the test, by wrapping them in an outer transaction (really using
    Postgres savepoints).
    """

    async with test_db_engine.connect() as connection:
        async with connection.begin() as outer_transaction:
            session = AsyncSession(connection)
            await session.begin_nested()

            yield session

            await session.close()
            await outer_transaction.rollback()
