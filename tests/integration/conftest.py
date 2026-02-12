import asyncio
from typing import Iterator

import pytest
from advanced_alchemy.extensions.litestar.plugins import (
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from litestar import Litestar
from litestar.testing import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncSessionTransaction,
    async_sessionmaker,
)
from testcontainers.postgres import PostgresContainer  # type: ignore

from create_app import create_app
from integration.helpers.test_data.db_setup import seed_test_db
from integration.helpers.test_data.test_users import test_users
from integration.helpers.test_data.types import FakeUser
from integration.helpers.utils.os_utils import temporarily_modified_environ
from integration.helpers.utils.req_utils import make_csrf_token_header

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
def test_app(test_db_container: PostgresContainer) -> Iterator[Litestar]:
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
        app = create_app()
        yield app


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
) -> FakeUser:
    """Logs in as one or more users before running the attached test; provides the
    user's email and id as a `FakeUser`.

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

    test_user = FakeUser(**rsp.json())
    return test_user


@pytest.fixture(autouse=True)
def transactional_test(
    test_client: TestClient[Litestar], monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """Run each test inside an outer DB transaction created in the app loop.

    The TestClient runs the app in a separate event loop (blocking portal).
    To avoid cross-loop connection affinity errors we create the connection
    and outer transaction inside that portal, then monkeypatch the app's
    session maker (stored in app.state by the SQLAlchemy plugin) to bind to
    the test connection. Requests in the test will commit into the outer
    transaction; at teardown we rollback the outer transaction which is fast
    and leaves the database clean for the next test.

    This fixture provided directly by @LonelyVikingMichael, a maintainer of
    litestar-users, via Litestar support Discord. Used almost verbatim with
    minimal changes, such as defining app and db_config and adding type hints.
    """

    app = test_client.app
    db_config: SQLAlchemyAsyncConfig = app.plugins.get(SQLAlchemyPlugin).config[0]

    # We'll wrap the session maker to start a nested SAVEPOINT for every
    # session created. This avoids global event listeners and works with
    # AsyncSession by using the underlying sync_session.begin_nested when
    # available (it's synchronous), otherwise we schedule the async
    # session.begin_nested coroutine on the running loop.

    def _start_transaction() -> None:
        async def _() -> None:
            # Get engine and create a connection and transaction in the app loop
            engine = app.state[db_config.engine_app_state_key]
            conn = await engine.connect()
            tx = await conn.begin()

            # Build a session maker that binds sessions to this connection
            session_kws = dict(db_config.session_config_dict)
            session_kws.setdefault("bind", conn)
            base_session_maker: async_sessionmaker[AsyncSession] = (
                db_config.session_maker_class(**session_kws)
            )

            # Wrap the session maker so each created AsyncSession starts a
            # nested transaction (SAVEPOINT). Prefer sync_session.begin_nested()
            # when present because it's synchronous and immediate.
            def session_factory() -> AsyncSession:
                sess = base_session_maker()
                sync = getattr(sess, "sync_session", None)
                if sync is not None:
                    # Start nested savepoint synchronously on the underlying
                    # sync Session so request handlers see the savepoint.
                    sync.begin_nested()
                else:
                    # Fallback: schedule the async begin_nested coroutine.
                    coro: AsyncSessionTransaction = sess.begin_nested()
                    try:
                        import asyncio

                        # not clear how coro can be passed to create_task when it's not
                        # actually a coroutine
                        asyncio.get_running_loop().create_task(coro)  # type: ignore[arg-type]
                    except Exception:
                        pass
                return sess

            test_session_maker = session_factory

            # Replace session maker in app.state so provide_session() uses it.
            monkeypatch.setitem(
                app.state, db_config.session_maker_app_state_key, test_session_maker
            )

            # Store test-specific objects for teardown
            app.state["_test_conn"] = conn
            app.state["_test_tx"] = tx

        return test_client.blocking_portal.call(_)

    # start transaction in app loop
    _start_transaction()

    try:
        yield
    finally:

        def _rollback_transaction() -> None:
            async def _() -> None:
                # rollback and close test connection
                tx = app.state.pop("_test_tx", None)
                conn = app.state.pop("_test_conn", None)
                if tx is not None:
                    try:
                        await tx.rollback()
                    except Exception:
                        # Rollback can fail if the connection is already closed due
                        # to a test error, so we catch and ignore exceptions here.
                        pass
                if conn is not None:
                    try:
                        await conn.close()
                    except Exception:
                        pass

            return test_client.blocking_portal.call(_)

        _rollback_transaction()
