from advanced_alchemy.base import UUIDBase
from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.litestar.plugins import SQLAlchemyAsyncConfig


def get_litestar_sqlalchemy_async_config(db_url):
    return SQLAlchemyAsyncConfig(
        connection_string=db_url,
        session_dependency_key="session",
        session_config=AsyncSessionConfig(expire_on_commit=False),
        before_send_handler="autocommit",
    )


async def on_startup_init_db(db_url):
    """Invoke from app startup to create all litestar_users db entities

    Sets up SQLAlchemy config, with `before_send_handler="autocommit"`
    """
    engine = get_litestar_sqlalchemy_async_config(db_url).get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(UUIDBase.metadata.create_all)
