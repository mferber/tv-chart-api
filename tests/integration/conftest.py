import asyncio
from typing import AsyncIterator, Iterator
from uuid import UUID

import pytest
import pytest_asyncio
from helpers.test_data.db_setup import seed_test_db
from helpers.test_data.test_users import test_users
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer  # type: ignore

from setup.litestar_users.models import User

TESTCONTAINER_POSTGRES_VERSION = 18


@pytest.fixture(scope="package")
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
async def user_id(request: pytest.FixtureRequest, test_db_engine: AsyncEngine) -> UUID:
    """Looks up the user ID for the given fake user tag.

    Parametrize the test as follows:

    ```
    @pytest.mark.parametrize('user_id', ["test_user1"], indirect=True)
    def test...():
        ...
    ```
    """

    test_user_tag = request.param
    test_user_info = test_users.get(test_user_tag)
    if test_user_info is None:
        raise KeyError(f"Test user '{test_user_tag}' not found")
    user_email = test_user_info[0]
    async with AsyncSession(test_db_engine) as session:
        q = select(User.id).filter_by(email=user_email)
        result: UUID | None = await session.scalar(q)
        if result is None:
            raise KeyError(f"Test user email '{user_email}' not in db")
        return result


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
